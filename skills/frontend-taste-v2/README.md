# Frontend Taste v2 (Anti-Slop) 🎨

A flagship agentic skill designed to enforce rigorous visual aesthetics, layout constraints, and micro-interaction standards for AI-generated UI code. 

**Say goodbye to "AI Slop."**

This skill equips your LLM / AI coding agents (like Claude, Gemini, or Antigravity) with a robust "design director" persona. It prevents the generation of generic, unimaginative layouts (e.g., identical 3-column bento boxes, overuse of primary purple gradients, unconsidered typographic hierarchy) and instead guides the agent to produce distinctive, high-end, production-ready interfaces.

## 🌟 Key Features

- **The "Anti-Slop" Manifesto**: Blocks overused AI visual tropes automatically (e.g. no random emojis as UI icons, no default blue/purple gradients).
- **Design Variance Controls**: Explicitly manages how "wild" or "restrained" a layout should be based on the industry.
- **Motion Intensity Variables**: Provides specific physics parameters for CSS and Framer Motion.
- **Visual Density Adjustments**: Enforces deliberate whitespace and structural alignment (no accidental uneven padding).
- **Tooling Integrations**: Designed to pair flawlessly with Tailwind CSS, React, and Next.js.

## 📦 Installation (Antigravity)

1. Clone or download this repository into your local skills directory:
   ```bash
   cd ~/.gemini/config/skills/
   git clone https://github.com/YOUR_USERNAME/frontend-taste-v2.git
   ```

2. Ensure your agent can access it by registering it in your `skills.config.json` (if applicable) or relying on standard directory discovery.

## 🚀 Usage

Once installed, simply append instructions like this when asking your agent to build UI:

> "Build a modern pricing page for a SaaS product. **Please strictly follow the `frontend-taste-v2` design guidelines.**"

For advanced use cases, you can integrate this skill into your `teamwork`, `code-review`, and `agy-studio` workflows to enforce design constraints across multiple agents.

## ⚖️ License

MIT License.
