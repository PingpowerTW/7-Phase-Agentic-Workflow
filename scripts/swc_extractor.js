#!/usr/bin/env node
/**
 * swc_extractor.js — Deterministic AST Feature Extractor powered by @swc/core
 *
 * 【設計目標】
 * 1. 取代正則表達式，提供 100% 精確的 JS/TS 抽象語法樹 (AST) 抽取。
 * 2. 支援單檔解析 (`node swc_extractor.js <file>`) 與 `--batch` 串流模式（由 stdin 接收檔案清單）。
 * 3. 避免 Windows 上千次 Process Spawn 風暴，批次模式下於單一 Node 處理序內完成。
 * 4. 抽取四大拓撲實體：definitions (函數/類別/方法/箭頭函數)、imports (靜態/動態/require)、
 *    exports (命名/預設/重導出)、calls (函數呼叫邊)。
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

let swc;
try {
  swc = require('@swc/core');
} catch (err) {
  process.stderr.write(JSON.stringify({
    error: 'MISSING_DEPENDENCY',
    message: '@swc/core is not installed. Please run npm install --save-dev @swc/core'
  }) + '\n');
  process.exit(2);
}

/**
 * 建立原始碼行號索引，提供 O(log N) 的 Byte Offset 轉行號查詢
 */
function buildLineIndex(source) {
  const lineStarts = [0];
  for (let i = 0; i < source.length; i++) {
    if (source[i] === '\n') {
      lineStarts.push(i + 1);
    }
  }
  return lineStarts;
}

/**
 * 依據 Byte Offset 進行二分搜尋計算 1-indexed 行號
 */
function getLineNumber(offset, lineStarts, baseSpanStart = 0) {
  if (typeof offset !== 'number' || offset < 0) return 1;
  const relOffset = Math.max(0, offset - baseSpanStart);
  let low = 0;
  let high = lineStarts.length - 1;
  while (low <= high) {
    const mid = (low + high) >> 1;
    if (lineStarts[mid] <= relOffset) {
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }
  return high + 1;
}

/**
 * 遞迴展開 MemberExpression 成點狀呼叫路徑 (如 console.log, this.service.fetch)
 */
function extractMemberExpr(node) {
  if (!node) return '';
  if (node.type === 'Identifier') return node.value;
  if (node.type === 'ThisExpression') return 'this';
  if (node.type === 'MemberExpression') {
    const obj = extractMemberExpr(node.object);
    const prop = node.property ? (node.property.value || node.property.name || '') : '';
    return obj ? `${obj}.${prop}` : prop;
  }
  return '';
}

/**
 * 解析單一 JavaScript / TypeScript 原始碼檔案
 */
function parseFile(filePath) {
  const normPath = filePath.replace(/\\/g, '/');
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lineStarts = buildLineIndex(content);

    const ext = path.extname(filePath).toLowerCase();
    const isTs = ext === '.ts' || ext === '.tsx' || ext === '.mts' || ext === '.cts';
    const isJsx = ext === '.jsx' || ext === '.tsx';

    const parserOptions = isTs
      ? {
          syntax: 'typescript',
          tsx: isJsx,
          decorators: true,
          dynamicImport: true,
        }
      : {
          syntax: 'ecmascript',
          jsx: isJsx,
          decorators: true,
          dynamicImport: true,
        };

    const ast = swc.parseSync(content, parserOptions);
    const baseSpanStart = (ast.span && typeof ast.span.start === 'number') ? ast.span.start : 0;

    const definitions = [];
    const imports = [];
    const exportsList = [];
    const calls = [];

    const callerStack = [];
    let currentClassName = null;

    function walk(node, parent = null) {
      if (!node || typeof node !== 'object') return;

      let pushedCaller = false;
      const prevClass = currentClassName;

      // 1. 類別定義 (ClassDeclaration)
      if (node.type === 'ClassDeclaration' && node.identifier) {
        const clsName = node.identifier.value;
        currentClassName = clsName;
        definitions.push({
          name: clsName,
          type: 'class',
          line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
        });
      }

      // 2. 函數宣告 (FunctionDeclaration)
      else if (node.type === 'FunctionDeclaration' && node.identifier) {
        const fnName = node.identifier.value;
        definitions.push({
          name: fnName,
          type: 'function',
          line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
        });
        callerStack.push(fnName);
        pushedCaller = true;
      }

      // 3. 類別方法與建構子 (ClassMethod / Constructor)
      else if (node.type === 'ClassMethod' && node.key) {
        const methodName = node.key.value || node.key.name || 'method';
        const fullName = currentClassName ? `${currentClassName}.${methodName}` : methodName;
        definitions.push({
          name: fullName,
          type: 'method',
          line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
        });
        callerStack.push(fullName);
        pushedCaller = true;
      } else if (node.type === 'Constructor') {
        const fullName = currentClassName ? `${currentClassName}.constructor` : 'constructor';
        definitions.push({
          name: fullName,
          type: 'method',
          line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
        });
        callerStack.push(fullName);
        pushedCaller = true;
      }

      // 4. 變數賦值型箭頭函數 (VariableDeclarator: const fn = () => {})
      else if (node.type === 'VariableDeclarator' && node.id && node.id.type === 'Identifier') {
        const varName = node.id.value;
        if (node.init && (node.init.type === 'ArrowFunctionExpression' || node.init.type === 'FunctionExpression')) {
          definitions.push({
            name: varName,
            type: 'function',
            line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
          });
          callerStack.push(varName);
          pushedCaller = true;
        }
      }

      // 5. 靜態 Import 宣告 (ImportDeclaration)
      else if (node.type === 'ImportDeclaration' && node.source) {
        const src = node.source.value;
        const specifiers = [];
        if (Array.isArray(node.specifiers)) {
          for (const s of node.specifiers) {
            if (s.type === 'ImportDefaultSpecifier' && s.local) {
              specifiers.push(s.local.value);
            } else if (s.type === 'ImportNamespaceSpecifier' && s.local) {
              specifiers.push(`* as ${s.local.value}`);
            } else if (s.type === 'ImportSpecifier' && s.local) {
              specifiers.push(s.local.value);
            }
          }
        }
        imports.push({
          source: src,
          specifiers,
          kind: 'static',
          line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
        });
      }

      // 6. Export 宣告
      else if (node.type === 'ExportDeclaration' && node.declaration) {
        const d = node.declaration;
        if (d.type === 'FunctionDeclaration' && d.identifier) {
          exportsList.push({
            name: d.identifier.value,
            type: 'function',
            line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
          });
        } else if (d.type === 'ClassDeclaration' && d.identifier) {
          exportsList.push({
            name: d.identifier.value,
            type: 'class',
            line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
          });
        } else if (d.type === 'VariableDeclaration' && Array.isArray(d.declarations)) {
          for (const decl of d.declarations) {
            if (decl.id && decl.id.type === 'Identifier') {
              const isFn = decl.init && (decl.init.type === 'ArrowFunctionExpression' || decl.init.type === 'FunctionExpression');
              exportsList.push({
                name: decl.id.value,
                type: isFn ? 'function' : 'variable',
                line: getLineNumber(decl.span.start, lineStarts, baseSpanStart)
              });
            }
          }
        }
      } else if (node.type === 'ExportNamedDeclaration') {
        const src = node.source ? node.source.value : null;
        if (Array.isArray(node.specifiers)) {
          for (const s of node.specifiers) {
            const expName = (s.exported && s.exported.value) || (s.orig && s.orig.value) || 'unknown';
            exportsList.push({
              name: expName,
              type: 'named',
              source: src,
              line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
            });
          }
        }
      } else if (node.type === 'ExportDefaultDeclaration') {
        exportsList.push({
          name: 'default',
          type: 'default',
          line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
        });
      }

      // 7. 呼叫表達式 (CallExpression)
      else if (node.type === 'CallExpression') {
        // dynamic import()
        if (node.callee && node.callee.type === 'Import' && Array.isArray(node.arguments) && node.arguments[0]) {
          const arg = node.arguments[0].expression || node.arguments[0];
          if (arg && arg.type === 'StringLiteral') {
            imports.push({
              source: arg.value,
              specifiers: [],
              kind: 'dynamic',
              line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
            });
          }
        }
        // CommonJS require()
        else if (node.callee && node.callee.type === 'Identifier' && node.callee.value === 'require') {
          if (Array.isArray(node.arguments) && node.arguments[0]) {
            const arg = node.arguments[0].expression || node.arguments[0];
            if (arg && arg.type === 'StringLiteral') {
              imports.push({
                source: arg.value,
                specifiers: [],
                kind: 'require',
                line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
              });
            }
          }
        }
        // 函數/方法呼叫
        else {
          let calleeName = '';
          if (node.callee && node.callee.type === 'Identifier') {
            calleeName = node.callee.value;
          } else if (node.callee && node.callee.type === 'MemberExpression') {
            calleeName = extractMemberExpr(node.callee);
          }

          if (calleeName) {
            const currentCaller = callerStack.length > 0 ? callerStack[callerStack.length - 1] : '(top-level)';
            calls.push({
              caller: currentCaller,
              callee: calleeName,
              line: getLineNumber(node.span.start, lineStarts, baseSpanStart)
            });
          }
        }
      }

      // 走訪子節點
      for (const k of Object.keys(node)) {
        if (k === 'span') continue;
        const val = node[k];
        if (Array.isArray(val)) {
          for (const item of val) {
            walk(item, node);
          }
        } else if (val && typeof val === 'object' && val.type) {
          walk(val, node);
        }
      }

      if (pushedCaller) {
        callerStack.pop();
      }
      currentClassName = prevClass;
    }

    walk(ast);

    return {
      file: normPath,
      definitions,
      imports,
      exports: exportsList,
      calls,
      error: null
    };
  } catch (err) {
    return {
      file: normPath,
      definitions: [],
      imports: [],
      exports: [],
      calls: [],
      error: err.message || String(err)
    };
  }
}

async function main() {
  const args = process.argv.slice(2);
  const isBatch = args.includes('--batch');

  if (isBatch) {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: false
    });

    const lines = [];
    for await (const line of rl) {
      if (line.trim()) lines.push(line.trim());
    }

    let filePaths = [];
    const fullInput = lines.join('\n').trim();
    if (fullInput.startsWith('[') && fullInput.endsWith(']')) {
      try {
        filePaths = JSON.parse(fullInput);
      } catch {
        filePaths = lines;
      }
    } else {
      filePaths = lines;
    }

    const results = [];
    for (const fp of filePaths) {
      if (fp && fs.existsSync(fp)) {
        results.push(parseFile(fp));
      }
    }

    process.stdout.write(JSON.stringify(results, null, 2) + '\n');
  } else {
    const targetFile = args.find(a => !a.startsWith('--'));
    if (!targetFile) {
      process.stderr.write('Usage: node swc_extractor.js <file_path> [--batch]\n');
      process.exit(1);
    }

    if (!fs.existsSync(targetFile)) {
      process.stderr.write(`File not found: ${targetFile}\n`);
      process.exit(1);
    }

    const result = parseFile(targetFile);
    process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  }
}

if (require.main === module) {
  main();
}

module.exports = { parseFile };
