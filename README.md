# MongoDB AI Agent

**Hello All, Welcome to the MongoDB AI Agent!**

This agent integrates with your MongoDB instance using advanced **RAG** (Retrieval-Augmented Generation) capabilities. It supports the **GGUF Qwen2.5**, **GGUF Gemma3 models**, **GeminiAPI**, and all **Ollama models (LiteLLM)**.

**If you have R1 models in GGUF format, please rename the models to include the keyword "R1". :)**

**There are Turkish example prompts in the prompts.yaml file — you can customize them according to your own needs.**

---

### Prerequisites

Before using the agent, make sure you have the following:

1. **Python 3.9 (minimum)** installed on your system.
2. **.env** file configured for your application. If you're unsure how to create it, follow the instructions below.
3. **Required libraries** installed by running:  
   ```bash
   pip install -r requirements.txt
   ```

---

### Setup Guide

1. **Clone the Repository**

   Clone this repository to your local machine:
   ```bash
   git clone <repository_url>
   cd <repository_name>
   ```

2. **Configure Your Environment**

   - Copy the `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```

   - Open `.env` and make any necessary changes (e.g., MongoDB connection details).

3. **Run the Application**

   Start the application:
   ```bash
   python main.py
   ```

4. **Schema Creation (First-Time Setup)**

   Upon running the application for the first time, two important files will be automatically created:
   - `mongo_schema_doc.yaml`
   - `mongo_schema.json`

   These files will be stored in the root directory.

5. **Customize Your Schema**

   - Open the **`mongo_schema_doc.yaml`** file.
   - **Important:** Customize this file to correctly match your MongoDB collections. This is essential for RAG to properly map your collections.
   - It's highly recommended to follow the example folder's format to avoid issues.

6. **Delete the Old FAISS Index**

   After updating your `mongo_schema_doc.yaml`, delete the old FAISS index by removing the `faiss_mongo_schema` folder. Then, **restart the application**.

---

### How It Works

1. **FAISS Index Creation**

   Once the application restarts, a new FAISS index will be generated based on the updated `mongo_schema_doc.yaml` file. This index will be used for querying and analysis.

2. **Choose Your Model**

   The agent will prompt you to choose a **model type**. You can choose from:
   - **GGUF Qwen2.5**
   - **GGUF Gemma3**
   - **GeminiAPI**
   - **Ollama (LiteLLM)**

   The model selection determines how your queries will be processed and which model will analyze the data.

3. **Run Queries**

   Once the index is ready and the model is selected, you can start running your queries. The system will guide you step-by-step, making it easy to analyze your MongoDB collections and execute various operations based on your inputs.

---

### Application Flow

1. **Step 1:** Configure your `.env` and run the application.
2. **Step 2:** Customize your `mongo_schema_doc.yaml` to map your collections correctly.
3. **Step 3:** Delete the old FAISS index and restart the application.
4. **Step 4:** Choose a model type and start running queries on your MongoDB data.

The agent will walk you through these steps, ensuring a smooth experience with **feedback and guidance** throughout the process.

---

### Important Notes

- **RAG (Retrieval-Augmented Generation)** is key to the agent's functionality. Ensure that the schema is correctly configured to allow the agent to query the right data.
- **MongoDB Collections:** Ensure the schema maps your collections accurately for optimal results.
- **FAISS Index:** The FAISS index is crucial for the retrieval process. After schema updates, deleting and regenerating the index ensures the best accuracy.

---

### Support

If you encounter any issues or need help, feel free to reach out by opening an **Issue**, or contact us at **[linkedin](https://www.linkedin.com/in/erythropygia/)** for further assistance.
