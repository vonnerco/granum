AI Engineer Assessment Start 10:45am EST

**Architecture**

Pre-requistes:

1. Saved Granum's email and assessment pdf (for quick reference in IDE)
2. Created Isolated folder in VS Code
3. Obtained Gemini free API Key (tested to ensure it works)
4. Created .env file to stored Gemini API Key
5. Created virtual environment to isolate dependencies
   1. ran Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   2. to Temporarily allow scripts for this specific session
6. Activated virtual environment in terminal

Folder Structure:

1. Spinned up codex vs code editor extension
   1. used LLM GPT 5.3 Codex High Reasoning
   2. this model was developed for precise tasks such as
      1. generating/editing code, creating files and managing folder structure
2. Structured folder and files for project
   1. used arena.ai direct model mode for ad hoc comprehensive file structuring
      1. I prompt engineered specific instuction and asked my gemini-2.5-pro llm to give me a stucuted .md file that architected my Granum's project entire file structure (i edited the final structure to ensure proper arhcitecture)
   2. created a file named file_architecture.md so that codex could easily create my desired file structure for Granum project

**Requirements**

1. Created requirements.txt file (used arena.ai gemini-2.5-pro llm) to give me the python libraries and modules needed to complete this task0000
