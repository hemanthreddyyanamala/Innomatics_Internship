Phase 1: Environment & API Foundation

[ ] Initialize Git repository and .gitignore (exclude .env).

[ ] Set up Python virtual environment and requirements.txt.

[ ] Implement GeminiClient module (API integration with google-generativeai).

[ ] Configure environment variable handling for API Keys.

[ ] Implement basic exception handling and logging for API calls.

Phase 2: Backend Logic & Context

[ ] Build Session Memory Manager for multi-turn history.

[ ] Implement token count tracking and optimization.

[ ] Create PromptManager for role-based system instructions.

[ ] Define domain-specific constraints (e.g., Financial/Medical disclaimers).

[ ] Test backend logic via CLI to ensure context retention.

Phase 3: Streamlit UI Development

[ ] Design layout (Sidebar for settings, main chat window).

[ ] Implement st.chat_message for user and assistant bubbles.

[ ] Add real-time response streaming and loading spinners.

[ ] Integrate UI with the modular backend (No business logic in app.py).

[ ] Implement "Clear Chat" and "Session Export" features.

Phase 4: Production Hardening

[ ] Conduct "Red Teaming" (Testing for prompt injection/out-of-scope queries).

[ ] Refine error fallback mechanisms (Graceful degradation).

[ ] Finalize modular directory structure (/src, /prompts, /assets).

[ ] Generate comprehensive README.md with architecture diagrams.

Phase 5: AWS EC2 Deployment

[ ] Launch EC2 Instance (t3.micro or higher) and SSH access.

[ ] Configure Security Groups (Inbound rules for Port 8501).

[ ] Clone repository and set up server-side environment variables.

[ ] Deploy application using a process manager (e.g., tmux or systemd).

[ ] Verify Public IP accessibility and final end-to-end testing.