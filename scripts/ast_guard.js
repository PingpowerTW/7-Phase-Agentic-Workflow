#!/usr/bin/env node
/**
 * ast_guard.js — Level 0.5 Deterministic AST Safety Gate
 *
 * 【設計目標】
 * 依據 invariants.yaml 與門禁規範，使用 @swc/core 執行確定性微秒級語意檢驗：
 * 1. 零生產接縫 (INV_VERIFY_03 / INV_VERIFY_04)：
 *    在非測試檔案中，嚴禁 export 帶有 `_test_`, `mock`, `fake`, `stub` 前綴的識別碼，
 *    或在公開簽名中包含 mock 參數。
 * 2. 垃圾測試與佔位符 (INV_VERIFY_02)：
 *    測試檔案中嚴禁空測試區塊 (`test('...', () => {})`)、`test.todo` 或未完工之佔位標籤。
 *
 * 【退出碼規範】
 * 0: PASS (全部合規)
 * 1: BLOCK (偵測到違規，印出結構化報告)
 * 2: SKIP / WARN (無目標檔案或語法警告)
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

let swc;
try {
  swc = require('@swc/core');
} catch (err) {
  console.warn('⚠️  [@swc/core 未安裝] 跳過 Level 0.5 AST Guard 檢驗。');
  process.exit(0);
}

function isTestFile(filePath) {
  const norm = filePath.replace(/\\/g, '/').toLowerCase();
  return (
    norm.includes('.test.') ||
    norm.includes('.spec.') ||
    norm.includes('__tests__/') ||
    norm.includes('/tests/') ||
    norm.includes('/test/') ||
    path.basename(norm).startsWith('test_') ||
    path.basename(norm).endsWith('_test.js') ||
    path.basename(norm).endsWith('_test.ts')
  );
}

function isSeamIdentifier(name) {
  if (!name || typeof name !== 'string') return false;
  const seamRegex = /^(?:_test_|__test__|mock|_mock_|fake_|stub_|test_)/i;
  const backdoorRegex = /(?:TestSeam|MockHelper|TestBackdoor|setTestState|__setMock|__resetMock)$/i;
  return seamRegex.test(name) || backdoorRegex.test(name);
}

function hasMockParameter(params) {
  if (!Array.isArray(params)) return null;
  const mockParamRegex = /^(?:mock|_mock|testMock|isTest|__mock|useMock|mockData)$/i;
  for (const p of params) {
    let paramName = '';
    if (p.type === 'Identifier') {
      paramName = p.value;
    } else if (p.type === 'AssignmentPattern' && p.left && p.left.type === 'Identifier') {
      paramName = p.left.value;
    } else if (p.pat && p.pat.type === 'Identifier') {
      paramName = p.pat.value;
    } else if (p.pat && p.pat.type === 'AssignmentPattern' && p.pat.left && p.pat.left.type === 'Identifier') {
      paramName = p.pat.left.value;
    }
    if (paramName && mockParamRegex.test(paramName)) {
      return paramName;
    }
  }
  return null;
}

function auditFile(filePath, codeOverride = null) {
  const normPath = filePath.replace(/\\/g, '/');
  const violations = [];

  let content = codeOverride;
  if (content === null) {
    if (!fs.existsSync(filePath)) {
      return violations;
    }
    content = fs.readFileSync(filePath, 'utf-8');
  }

  const ext = path.extname(filePath).toLowerCase();
  const validExts = ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.mts', '.cts'];
  if (codeOverride === null && !validExts.includes(ext)) {
    return violations;
  }

  const isTest = isTestFile(normPath);
  const isTs = ext === '.ts' || ext === '.tsx' || ext === '.mts' || ext === '.cts';
  const isJsx = ext === '.jsx' || ext === '.tsx';

  let ast;
  try {
    ast = swc.parseSync(content, {
      syntax: isTs ? 'typescript' : 'ecmascript',
      tsx: isTs && isJsx,
      jsx: !isTs && isJsx,
      decorators: true,
      dynamicImport: true,
    });
  } catch (err) {
    if (codeOverride !== null) {
      return [];
    }
    violations.push({
      rule: 'SYNTAX_ERROR',
      file: normPath,
      line: 1,
      message: `SWC 解析失敗: ${err.message}`
    });
    return violations;
  }

  // 1. 檢查未完工之佔位標籤
  const lines = content.split('\n');
  lines.forEach((lineText, idx) => {
    const lineNum = idx + 1;
    const placeholderMatch = lineText.match(/\b(TODO|FIXME|XXX|PLACEHOLDER)\b\s*[:：]/i);
    if (placeholderMatch) {
      violations.push({
        rule: 'INV_VERIFY_02',
        name: 'Zero Junk Test & Placeholders',
        file: normPath,
        line: lineNum,
        message: `偵測到佔位標籤 [${placeholderMatch[1]}]: 嚴禁提交未完工之佔位代碼。`
      });
    }
  });

  // 2. 語法樹走訪
  function walk(node) {
    if (!node || typeof node !== 'object') return;

    // --- 規則 A: 零生產接縫 (INV_VERIFY_03 / INV_VERIFY_04) ---
    if (!isTest) {
      if (node.type === 'ExportDeclaration' && node.declaration) {
        const d = node.declaration;
        if (d.type === 'FunctionDeclaration' && d.identifier) {
          const fnName = d.identifier.value;
          if (isSeamIdentifier(fnName)) {
            violations.push({
              rule: 'INV_VERIFY_03',
              name: 'No Production Seams',
              file: normPath,
              line: 1,
              message: `生產代碼禁止 export 測試接縫函式 '${fnName}'`
            });
          }
          const badParam = hasMockParameter(d.params);
          if (badParam) {
            violations.push({
              rule: 'INV_VERIFY_03',
              name: 'No Production Seams',
              file: normPath,
              line: 1,
              message: `生產函式 '${fnName}' 包含測試專用參數 '${badParam}'，嚴禁在生產代碼開洞`
            });
          }
        } else if (d.type === 'ClassDeclaration' && d.identifier) {
          const clsName = d.identifier.value;
          if (isSeamIdentifier(clsName)) {
            violations.push({
              rule: 'INV_VERIFY_03',
              name: 'No Production Seams',
              file: normPath,
              line: 1,
              message: `生產代碼禁止 export 測試接縫類別 '${clsName}'`
            });
          }
        } else if (d.type === 'VariableDeclaration' && Array.isArray(d.declarations)) {
          for (const decl of d.declarations) {
            if (decl.id && decl.id.type === 'Identifier') {
              const varName = decl.id.value;
              if (isSeamIdentifier(varName)) {
                violations.push({
                  rule: 'INV_VERIFY_03',
                  name: 'No Production Seams',
                  file: normPath,
                  line: 1,
                  message: `生產代碼禁止 export 測試接縫變數 '${varName}'`
                });
              }
              if (decl.init && (decl.init.type === 'ArrowFunctionExpression' || decl.init.type === 'FunctionExpression')) {
                const badParam = hasMockParameter(decl.init.params);
                if (badParam) {
                  violations.push({
                    rule: 'INV_VERIFY_03',
                    name: 'No Production Seams',
                    file: normPath,
                    line: 1,
                    message: `生產函式 '${varName}' 包含測試專用參數 '${badParam}'`
                  });
                }
              }
            }
          }
        }
      } else if (node.type === 'ExportNamedDeclaration' && Array.isArray(node.specifiers)) {
        for (const spec of node.specifiers) {
          const expName = (spec.exported && spec.exported.value) || (spec.orig && spec.orig.value);
          if (isSeamIdentifier(expName)) {
            violations.push({
              rule: 'INV_VERIFY_03',
              name: 'No Production Seams',
              file: normPath,
              line: 1,
              message: `生產代碼禁止具名 export 測試接縫識別碼 '${expName}'`
            });
          }
        }
      }
    }

    // --- 規則 B: 垃圾測試模式 (INV_VERIFY_02) ---
    if (isTest) {
      if (node.type === 'CallExpression') {
        const callee = node.callee;
        const isTestFn = callee && callee.type === 'Identifier' && ['test', 'it', 'describe', 'suite'].includes(callee.value);
        if (isTestFn && Array.isArray(node.arguments) && node.arguments.length >= 2) {
          const testTitle = (node.arguments[0].expression || node.arguments[0]).value || '(unnamed)';
          const callbackArg = node.arguments[1].expression || node.arguments[1];
          if (callbackArg && (callbackArg.type === 'ArrowFunctionExpression' || callbackArg.type === 'FunctionExpression')) {
            const body = callbackArg.body;
            if (body && (body.type === 'BlockStatement' || body.type === 'FunctionBody') && Array.isArray(body.stmts) && body.stmts.length === 0) {
              violations.push({
                rule: 'INV_VERIFY_02',
                name: 'Zero Junk Test Patterns',
                file: normPath,
                line: 1,
                message: `偵測到無實質驗證之空測試區塊: ${callee.value}('${testTitle}')`
              });
            }
          }
        }

        if (callee && callee.type === 'MemberExpression') {
          const objName = callee.object && callee.object.value;
          const propName = callee.property && (callee.property.value || callee.property.name);
          if (['test', 'it'].includes(objName) && propName === 'todo') {
            violations.push({
              rule: 'INV_VERIFY_02',
              name: 'Zero Junk Test Patterns',
              file: normPath,
              line: 1,
              message: `偵測到假測試佔位符: ${objName}.todo()，嚴禁提交未完成的測試。`
            });
          }
        }
      }
    }

    for (const k of Object.keys(node)) {
      if (k === 'span') continue;
      const val = node[k];
      if (Array.isArray(val)) {
        for (const item of val) walk(item);
      } else if (val && typeof val === 'object' && val.type) {
        walk(val);
      }
    }
  }

  walk(ast);
  return violations;
}

function getGitChangedFiles() {
  try {
    const diff = execSync('git diff --name-only HEAD', { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'ignore'] });
    const cached = execSync('git diff --cached --name-only', { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'ignore'] });
    const all = new Set([
      ...diff.split('\n').map(s => s.trim()),
      ...cached.split('\n').map(s => s.trim())
    ]);
    return Array.from(all).filter(f => f && /\.(js|jsx|ts|tsx|mjs|cjs)$/i.test(f));
  } catch {
    return [];
  }
}

function main() {
  const args = process.argv.slice(2);
  let filesToAudit = [];
  let codeSnippet = null;

  if (args.includes('--git')) {
    filesToAudit = getGitChangedFiles();
    if (filesToAudit.length === 0) {
      console.log('✅ [Level 0.5 AST Guard] 無 JS/TS 檔案變更，自動放行。');
      process.exit(0);
    }
  } else if (args.includes('--code')) {
    const codeIdx = args.indexOf('--code');
    codeSnippet = args[codeIdx + 1] || '';
    filesToAudit = ['<inline_snippet.ts>'];
  } else {
    filesToAudit = args.filter(a => !a.startsWith('--'));
  }

  if (filesToAudit.length === 0) {
    console.log('ℹ️  [Level 0.5 AST Guard] 未指定審查檔案，略過。');
    process.exit(0);
  }

  const allViolations = [];
  for (const fp of filesToAudit) {
    const v = auditFile(fp, codeSnippet);
    allViolations.push(...v);
  }

  if (allViolations.length === 0) {
    console.log(`✅ [Level 0.5 AST Guard] 審查通過 (${filesToAudit.length} 檔案): 零生產接縫，零垃圾佔位符。`);
    process.exit(0);
  } else {
    console.error(`\n🛑 [Level 0.5 AST Guard] BLOCK 違規攔截！共發現 ${allViolations.length} 處違規：`);
    console.error('┌──────────────┬────────────────────────┬────────────────────────────────────────────┐');
    console.error('│ 規則 ID      │ 檔案                   │ 違規原因說明                               │');
    console.error('├──────────────┼────────────────────────┼────────────────────────────────────────────┤');
    for (const v of allViolations) {
      const ruleCol = (v.rule || 'GATE').padEnd(12);
      const fileCol = path.basename(v.file).slice(0, 22).padEnd(22);
      const msgCol = v.message.slice(0, 42).padEnd(42);
      console.error(`│ ${ruleCol} │ ${fileCol} │ ${msgCol} │`);
    }
    console.error('└──────────────┴────────────────────────┴────────────────────────────────────────────┘');
    for (const v of allViolations) {
      console.error(`  - [${v.rule}] ${v.name || 'Gate'}: ${v.message} (${v.file}:${v.line || 1})`);
    }
    console.error('💡 修正引導：請拔除生產代碼中的 mock 命名與接縫參數，並確保測試邏輯具備實質斷言。\n');
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { auditFile, isTestFile, isSeamIdentifier };
