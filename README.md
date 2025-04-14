```markdown
# MongoDB AI Agent

**Hello All, Welcome to the MongoDB AI Agent!** 🚀

This agent is built to integrate with your MongoDB instance using advanced **RAG** (Retrieval-Augmented Generation) capabilities. It supports the **GGUF Qwen2.5**, **Gemma3 models**, **GeminiAPI**, and all **Ollama models (LiteLLM)**.

---

### Prerequisites

Before you start using the agent, make sure you have the following:

1. **Python 3.9 (minimum)** installed on your system.
2. **.env** file configured for your application. If you're unsure how to create it, follow the instructions below.

---

### Setup Guide

1. **Clone the Repository:**

   First, clone this repository to your local machine:

   ```bash
   git clone <repository_url>
   cd <repository_name>
   ```

2. **Configure Your Environment:**

   - Copy the `.env.example` to `.env`:

     ```bash
     cp .env.example .env
     ```

   - Open `.env` and make any necessary changes based on your environment (e.g., MongoDB connection details).

3. **Run the Application:**

   Run the application to get started:

   ```bash
   python main.py
   ```

4. **Schema Creation (First-Time Setup):**

   Upon running the application for the first time, the system will automatically create two important files:

   - `mongo_schema_doc.yaml`
   - `mongo_schema.json`

   These files will be stored in the root directory.

5. **Customize Your Schema:**

   - Open the **`mongo_schema_doc.yaml`** file.
   - **Important:** Customize this file to match your MongoDB collections correctly. This is a crucial step to ensure RAG can properly map your collections.
   - It's highly recommended that you follow the format in the example folder to avoid any issues.

6. **Delete the Old FAISS Index:**

   After updating your `mongo_schema_doc.yaml`, delete the old FAISS index by removing the `faiss_mongo_schema` folder. Then, **restart the application**.

---

### How It Works

1. **FAISS Index Creation:**

   Once the application restarts, a new FAISS index will be generated based on the updated `mongo_schema_doc.yaml` file. This index will be used for querying and analysis.

2. **Choose Your Model:**

   The agent will prompt you to choose a **model type**. You can choose from:

   - **GGUF Qwen2.5**
   - **GGUF Gemma3**
   - **GeminiAPI**
   - **Ollama (LiteLLM)**

   The model selection determines how your queries will be processed and which model will analyze the data.

3. **Run Queries:**

   Once the index is ready and the model is selected, you can start running your queries. The system will guide you step-by-step, making it easy to analyze your MongoDB collections and execute various operations based on your inputs.

---

### Application Flow

1. **Step 1:** Configure your `.env` and run the application.
2. **Step 2:** Customize your `mongo_schema_doc.yaml` to map your collections correctly.
3. **Step 3:** Delete the old FAISS index and restart the application.
4. **Step 4:** Choose a model type and start running queries on your MongoDB data.

The agent will walk you through these steps, ensuring a smooth experience. You will receive **feedback and guidance** throughout the process.

---

### Important Notes

- **RAG (Retrieval-Augmented Generation)** plays a key role in this agent. Make sure to have the correct schema to ensure the agent can query the right data.
- **MongoDB Collections:** Properly configure the schema to map collections accurately for best results.
- **FAISS Index:** The FAISS index is essential for the retrieval-based process. Deleting and regenerating it after schema updates ensures the best accuracy.

---

### Support

If you run into any issues or need help, feel free to reach out to our support team, or check the issues section of this repository for troubleshooting tips.
```
