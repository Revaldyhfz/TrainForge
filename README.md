## Use of GenAI

Generative AI tools were used during development of TrainForge. The declaration below covers their use across both the design document and the final web project.

**Tools used:**
- Claude (Anthropic) — Claude.ai web interface and Claude Code (CLI / VS Code extension)
- OpenAI gpt-5.4-mini — integrated into the application as the GenAI feature

**Where AI assisted me:**
- Initial database schema and DBML for the ER diagram (declared in design document)
- Frontend layout ideas and Tailwind class suggestions for mockups
- Boilerplate Django code (view scaffolding, form patterns, template structure)
- Debugging deployment configuration (Render, WhiteNoise, environment variables)
- Deployment, and integrating GenAI

**Where AI did not write code unsupervised:**
- All AI-generated code was reviewed, edited, and tested by me before being committed
- Business logic decisions (data model relationships, role authorisation flow, exercise type system) were my design
- Architecture choices are my own

## Login Credentials

Deployment URL: **https://trainforge.onrender.com**

(First request may take ~30 seconds — Render free tier spins down after idle.)

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `AdminPass123!` |
| Trainer | `james` | `TrainerPass123!` |
| Trainer | `amy` | `TrainerPass123!` |