import dspy
import chromadb
import pandas as pd
import itertools
import warnings
import re

# --- RAG Survey Paper Citations ---
# This script is informed by the principles and challenges outlined in modern RAG research.
# For a comprehensive overview, refer to:
# 1. Gao, Y., Xiong, Y., Gao, X., Jia, K., Pan, J., Bi, Y., ... & Sun, H. (2023).
#    Retrieval-Augmented Generation for Large Language Models: A Survey. arXiv preprint arXiv:2312.10997.
# 2. Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., ... & Kiela, D. (2020).
#    Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. Advances in Neural Information Processing Systems, 33, 9459-9474.
# 3. Ram, O., Levine, Y., Geva, M., Schijndel, M. V., Bogin, B., Leyton-Brown, K., ... & Berant, J. (2023).
#    In-context retrieval-augmented language models. arXiv preprint arXiv:2302.00083.

# Suppress verbose warnings for a cleaner output
warnings.filterwarnings('ignore')

# --- 1. Document & LLM Configuration ---

# Placeholder documents that will form our knowledge base.
# In a real scenario, these would be loaded from files.
DOCUMENTS = {
    "doc1.md": """
# The Future of Energy: Fusion Power
Fusion power is a proposed form of power generation that would generate
electricity by using heat from nuclear fusion reactions. In a fusion reaction,
two lighter atomic nuclei combine to form a heavier nucleus, while releasing
enormous amounts of energy. The most promising reaction for terrestrial fusion
power is the deuterium-tritium (D-T) reaction. Deuterium is a stable isotope of
hydrogen and can be extracted from seawater, making it an abundant fuel source.
Tritium is radioactive but can be bred from lithium, which is also plentiful.

The primary challenge is achieving 'ignition', the point at which the reaction
becomes self-sustaining. This requires confining a plasma at extreme temperatures
(over 100 million degrees Celsius) and pressures. Two main approaches are being
researched: magnetic confinement, as seen in tokamaks like ITER, and inertial
confinement, used at facilities like the National Ignition Facility (NIF).
Recent breakthroughs at NIF have demonstrated net energy gain for the first time,
a landmark achievement, though commercial viability is still decades away.
""",
    "doc2.md": """
# Introduction to Neural Networks
A neural network is a computational model inspired by the structure and function
of biological neural networks in animal brains. It consists of interconnected
nodes, or 'neurons', organized in layers. An input layer receives raw data, one
or more hidden layers process the data through weighted connections, and an
output layer produces the final result.

Each connection between neurons has a weight, which is adjusted during the
training process. Training involves feeding the network a large dataset of examples
(e.g., images labeled as 'cat' or 'dog'). The network makes a prediction, compares
it to the actual label, and calculates an error. This error is then propagated
backward through the network to adjust the weights in a process called
backpropagation, aiming to minimize future errors. The strength of neural networks
lies in their ability to learn complex patterns and relationships from data without
being explicitly programmed.
""",
    "doc3.md": """
# The Principles of Retrieval-Augmented Generation (RAG)
Retrieval-Augmented Generation (RAG) is an architecture that enhances the capabilities
of Large Language Models (LLMs) by integrating external knowledge. Instead of relying
solely on its internal, parametric memory from training, a RAG system first retrieves
relevant information from a knowledge base before generating a response.

The process typically involves two main stages:
1.  **Retrieval**: Given a user query, a retriever module searches a vectorized knowledge
    base (like a ChromaDB index) to find the most relevant text chunks or documents.
    This is often done using dense vector similarity search.
2.  **Generation**: The original query and the retrieved context are then passed together
    to a generator LLM. The model uses this context to formulate a more accurate,
    fact-based, and up-to-date answer.

This approach mitigates common LLM issues like hallucination and outdated knowledge,
making them more reliable for knowledge-intensive tasks. Key hyperparameters in a RAG
system include the chunking strategy for the documents, the number of retrieved
documents (top_k), and the choice of embedding model.
"""
}

def setup_lms():
    """Configures the generator and judge LLMs."""
    generator_lm = dspy.OllamaLocal(model='phi3:mini', max_tokens=512)

    try:
        # It's best to use a powerful, independent model as the judge.
        # Ensure your OPENAI_API_KEY is set as an environment variable.
        judge_lm = dspy.OpenAI(model='gpt-4o-mini', max_tokens=1024, model_type='chat')
        print("Using GPT-4o-mini as the judge for scoring.")
    except Exception:
        print("Warning: OpenAI API key not found or invalid.")
        print("Falling back to phi3:mini as the judge. Scores may be less reliable.")
        judge_lm = generator_lm

    return generator_lm, judge_lm

# --- 2. RAG Signature and Evaluation Metric ---

class RAGSignature(dspy.Signature):
    """Answers questions based on retrieved context."""
    context = dspy.InputField(desc="Facts and information to answer the question.")
    question = dspy.InputField()
    answer = dspy.OutputField(desc="A factual and concise answer.")

def llm_as_a_judge_metric(question, context, generated_answer, judge_lm):
    """Uses a powerful LLM to score the quality of a generated answer."""
    with dspy.settings.context(lm=judge_lm):
        eval_prompt = f"""
        **Task**: Evaluate the quality of a generated answer based on the provided context and question.

        **Evaluation Criteria**:
        1.  **Faithfulness (1-5)**: Does the answer strictly rely on information from the provided context?
            - 5: The answer is fully supported by the context.
            - 3: The answer is mostly supported but might make a small, logical leap.
            - 1: The answer contains information not found in the context (hallucination).
        2.  **Conciseness (1-5)**: Is the answer direct and to the point?
            - 5: The answer is very concise and directly addresses the question.
            - 3: The answer is a bit verbose but still on topic.
            - 1: The answer is rambling and contains irrelevant information.

        **Context**:
        ---
        {context}
        ---

        **Question**: "{question}"
        **Generated Answer**: "{generated_answer}"

        **Instructions**:
        Think step-by-step. First, analyze for faithfulness. Second, analyze for conciseness.
        Finally, provide your scores in the exact format:
        Faithfulness: [score], Conciseness: [score]
        """

        class JudgeSignature(dspy.Signature):
            evaluation_prompt = dspy.InputField()
            evaluation_output = dspy.OutputField()

        predictor = dspy.Predict(JudgeSignature)
        response = predictor(evaluation_prompt=eval_prompt).evaluation_output

        try:
            faithfulness = float(re.search(r"Faithfulness:.*?(\d\.?\d*)", response).group(1))
            conciseness = float(re.search(r"Conciseness:.*?(\d\.?\d*)", response).group(1))
            return (faithfulness + conciseness) / 2.0
        except (AttributeError, ValueError):
            return 2.5

# --- 3. Helper Functions ---

def chunk_text(text, chunk_size):
    """Splits text into chunks of a specified size."""
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield ' '.join(words[i:i + chunk_size])

# --- 4. Main Grid Search Logic ---

def main():
    """Runs the grid search over RAG hyperparameters and saves the ranked results."""
    print("--- Starting RAG Hyperparameter Sweep ---")

    generator_lm, judge_lm = setup_lms()

    hyperparameters = {
        'chunk_size': [256, 512],
        'top_k': [3, 5],
        'embedder': ['text-embedding-ada-002', 'bge-small-en-v1.5']
    }
    param_combinations = list(itertools.product(*hyperparameters.values()))
    all_results = []

    test_questions = [
        "What is the main challenge in achieving fusion power?",
        "How do neural networks learn?",
        "What are the two main stages of a RAG system?"
    ]

    for i, params in enumerate(param_combinations):
        chunk_size, top_k, embedder_name = params
        config_id = f"config_{i+1}"

        print(f"\n--- [{config_id}/{len(param_combinations)}] Testing Configuration ---")
        print(f"  Chunk Size: {chunk_size}, Top K: {top_k}, Embedder: {embedder_name}")

        chroma_client = chromadb.Client()

        if embedder_name == 'text-embedding-ada-002':
            try:
                embedding_model = dspy.OpenAI(model='text-embedding-ada-002')
            except Exception:
                print(f"  Skipping {embedder_name}: OPENAI_API_KEY not set.")
                continue
        else:
            embedding_model = dspy.SentenceTransformers(embedder_name)

        collection_name = f"rag_collection_{config_id}"
        collection = chroma_client.create_collection(name=collection_name)

        all_chunks = []
        doc_ids = []
        for doc_id, doc_content in DOCUMENTS.items():
            for chunk_num, chunk in enumerate(chunk_text(doc_content, chunk_size)):
                all_chunks.append(chunk)
                doc_ids.append(f"{doc_id}_chunk_{chunk_num}")

        with dspy.settings.context(lm=embedding_model):
            embeddings = embedding_model(all_chunks).tolist()

        collection.add(embeddings=embeddings, documents=all_chunks, ids=doc_ids)
        print(f"  Indexed {len(all_chunks)} chunks into ChromaDB collection '{collection_name}'.")

        retriever_model = dspy.retrieve.ChromaRM(
            collection_name=collection_name,
            persist_directory=None,
            embedding_function=embedding_model.func,
            k=top_k
        )

        dspy.settings.configure(lm=generator_lm, rm=retriever_model)
        rag_module = dspy.ChainOfThought(RAGSignature)

        config_scores = []
        for question in test_questions:
            prediction = rag_module(question=question)
            context_for_judge = "\n\n".join(prediction.context)
            score = llm_as_a_judge_metric(question, context_for_judge, prediction.answer, judge_lm)
            config_scores.append(score)

        avg_score = sum(config_scores) / len(config_scores)
        print(f"  Average Score: {avg_score:.2f} / 5.0")

        all_results.append({
            'chunk_size': chunk_size,
            'top_k': top_k,
            'embedder': embedder_name,
            'average_score': avg_score
        })

    if not all_results:
        print("\nNo results were generated. This might be due to a missing API key.")
        return

    results_df = pd.DataFrame(all_results)
    ranked_df = results_df.sort_values(by='average_score', ascending=False).reset_index(drop=True)
    output_filename = 'rag_results.csv'
    ranked_df.to_csv(output_filename, index=False)

    print(f"\n--- RAG Sweep Complete. Results saved to '{output_filename}' ---")
    print(ranked_df.to_markdown(index=True))

if __name__ == "__main__":
    main()
