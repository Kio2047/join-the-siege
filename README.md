# Heron Coding Challenge - File Classifier

## Getting started
### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed on your machine
### Running the app
Follow the steps below to clone, build, and run the application:
1. Clone the repository:
    ```shell
    git clone https://github.com/Kio2047/join-the-siege
    cd join-the-siege
    ```

2. Build the Docker image:
    ```shell
    docker build -t file-classifier .
    ```

3. Run application:
    ```shell
    docker run -p 5000:5000 file-classifier
    ```

4. Test the classifier using a tool like curl:
    ```shell
    curl -X POST -F 'file=@path_to_pdf.pdf' http://127.0.0.1:5000/classify_file
    ```

5. Run tests:
   ```shell
    docker run --rm file-classifier pytest tests/ -v
    ```


## Proposed classifier:
### Preface:
Interesting challenge! Learnt a lot. Very open-ended and quite tough to define a good scope that fulfils the criteria within the suggested time — looking forward to feedback.

### Some basic assumptions:
- Filenames do not contain sensitive information.
- File content may contain sensitive information.
- Files are not misleading, that is, the filename will not strongly indicate an incorrect document class. For example, a file named `invoice_john_smith.pdf` will be an invoice, not a driving license; a file named `john's_bank_statement.pdf` will be a bank statement, not an invoice. A filename can, however, still be unclear (e.g., `poorly_named.pdf`) — that is not considered misleading.

### Pipeline description:
To efficiently handle high volumes of files and increase throughput, the classifier uses a pipeline that applies increasingly expensive methods in stages. At each stage, it attempts to classify the file; if successful, the process short-circuits and a response is returned to the client. If the attempt fails, the file proceeds to the next stage in the pipeline, where a more resource-intensive classification method is applied. Rather than throwing the kitchen sink at the problem upfront, this approach tries to extract as much value as possible from cheap heuristics before escalating to more sophisticated, compute-intensive methods — ultimately minimising effort required for classification.

 [Here's a diagram of the pipeline](https://excalidraw.com/#json=B78eNaCpkUTajVqL_bC4X,z6DYS5KzBh88P1ysqegTBg).


The steps in the pipeline are as follows:
1) Ensure the file extension is supported. If it isn't, send a 4xx error to the client.
2) (classification step) Search in the filename for any text that matches a `filename_regex` pattern belonging to a document class. If a match is found, respond to the client with the classification.
3) (classification step) Search in the filename for any text that fuzzily matches a `fuzzy_keyword` belonging to a document class. If a match with a `fuzzy_score` above the specified threshold is found, respond with to the client with the classification.
4) Ensure the MIME type of the file and its extension are matching (allows us to verify the extension is correct prior prior to text extraction).
5) Extract file text content using the appropriate method for the file extension. Fall back on OCR for pdfs if machine-readable text is sparse.
6) (classification step) Search in the extracted text matches against the `content_regex` belonging to a document class. If sufficient matches are found for a given class, respond to the client with the classification.
7) (classification step) Pass the file content to an embedding-based logistic regression model. If a classification is made with sufficient confidence, respond to the client with the classification.
8) Save the file for manual review and send a 4xx error to the client.

### Discussion:
Some sections of the pipeline are fairly self explanatory (e.g., searching for a regex pattern in the filename), but others warrant more detail and discussion:

#### Step 6 (pattern matching file content)
For file text content matching, regex patterns we look to match in extracted text for a given document class are put into one of three categories:
1) Required: every single required term must appear when content matching.
2) Supporting: the appearance of supporting terms in and of itself isn't enough to give us confidence in a classification — these terms might be fairly generic, like "date of birth" or "expiry date". Their appearance in combination with the required terms, however, bolsters our confidence in the classification.
3) Negative: the appearance of negative terms immediately disqualifies the document from being assigned the document class.

A note on negative terms: these should be chosen selectively — their purpose is to reduce false positives by breaking ties in specific, high-confusion document class pairs with wording overlaps. In practice, we would group similar docs and add negative terms within a cluster where wording overlaps — not across the entire set of documents. This could be done by running the pipeline in production, building a confusion matrix, and picking out common misclassifications based on file content pattern matching. We would then add 1 - 3 negative term disqualifiers for each offending pair, ignoring pairs that never collide. To keep the list small and high-precision, we could use thresholds (e.g., the term must appear in >= 90% of the wrong class but <1% of the correct one). We might also prefer scores over hard disqualifications — for example, instead of negative terms killing a match, deduct 0.3-0.5 from the confidence, so that one stray word or term can't undermine otherwise strong positive evidence. Here though, for the sake of simplicity, a negative term results in an instant disqualification.

#### Step 7 (embedding-based logistic regression model)
Disclaimer for this section: I am not an ML engineer (yet) and not practised at assessing trade-offs between different ML approaches for a production app — please bear that in mind! With that said, I did some high-level research to assess my options at this stage, and came to the following conclusions.

For the final, and most expensive classification step, we use a classification model to infer the file's document class based on its text content. Due to the possibility of sensitive file content and consequent data privacy considerations, we must self-host the model rather than relying on third-parties. At a high level, this leaves us with four options:

1) Train a classifier from scratch.
2) Fine-tune a pretrained language processing model (e.g., BERT).
3) Use a larger language model for zero-shot classification with prompting (e.g., DeepSeek-V2).
4) Embed text using a pretrained embedding model (e.g., all-MiniLM-L6-v2), then classify the output vectors with a simple classification algorithm (e.g., logistic regression).

Option 1 was not realistically viable. Without a pretrained foundation, the model would need to learn not only how to classify documents, but also how to interpret language from the ground up. That would require huge amounts of high-quality, diverse training data (far beyond our document classes) and significant computational resources. Training would be slow, complex, and productionising the model would require substantial engineering for tuning, checkpointing, version control and deployment. Adapting the model to support a new document class would require additional fine-tuning, demanding more compute and large, high-quality datasets for the new class — not ideal for scaling to new industries.

Option 2 improves on this by starting with a model that already understands language, thereby eliminating the need for foundational training and reducing the data and compute required. However, it still shares many of option 1's drawbacks: a need for expensive fine-tuning for every new document class, careful hyperparameter tuning, and the effort of managing checkpointing and versions. Again, each new document class would require labelled examples of sufficient quality and diversity - not that feasible when relying on limited and synthetic data.

Option 3 would circumvent the need for additional data and training by using zero-shot prompting (e.g., "Classify this file as a bank statement, invoice, driving license, or unknown"). This approach would be great for scaling to new industries as we wouldn't need to retrain or modify our model when adopting new document classes. To perform well, however, this process would require an LLM with strong reasoning capabilities. That would necessitate either reliance on a third-party API (not an option here due to data privacy considerations), or that we host the model ourselves, which is very resource-intensive and would require powerful hardware with a highly capable GPU. That in turn would result in lower efficiency, higher latency, and much more compute per request — limiting throughput and scalability.

Option 4 — the approach I chose — strikes the best balance between performance and simplicity in this context. It uses an embedding model (here, all-MiniLM-L6-v2) to convert the extracted document text into a dense vector representing the text content's meaning. On top of the embedding model, a small and fast classification algorithm (here, logistic regression) is trained to map the output dense vector to a corresponding document class. Because the embedding model already understands the semantics of language, we need only a small number of labelled examples to train the classifier, and the quality of the training data is less critical. This makes the classifier quick to retrain (and thus more easily scalable for new industries and document classes), as well as more appropriate in contexts where training data is lacking in quantity and quality (as is the case with the generated synthetic data used here). This solution is also significantly faster and computationally cheaper than the other options — embedding models are intentionally lightweight, and the classification algorithm itself is a simple statistical model. This classifier is significantly faster than the other options, resulting in higher throughput, and also runs well on a modest CPU (no hefty GPU or large-scale infrastructure required), making it significantly cheaper and more scalable. Finally, its simple architecture makes it easy to deploy — the embedding model is versioned externally, and the classifier is just a small serialized object.

The classifier was trained on synthetic data for the driving license, bank statement, and invoice document classes. While the data was generated using scripts (see the `scripts/` directory) which aim to introduce some variety and noise, it remains highly simplified — a model trained on real-world data would generalise more effectively and achieve better classification performance.

#### Extensible config
To separate concerns, all of the supported document classes and their rules were externalised into a `industry_rules.yaml` file, and all of the supported document types and their matching MIME type(s) were externalised into a `supported_filetypes.yaml` file. Both of these files exist in the `src/classifier/config` directory. These two files contain default configuration data, which is validated and compiled when the server process is starting by `config_loader.py`.

To improve ease of adopting new document classes, when the server loads, `config_loader.py` looks for a `industry_rules.yaml` file and a `supported_filetypes.yaml` file in both a directory defined by the env variable `CLASSIFIER_CONFIG_DIR` and in a `config/` folder present in the working directory, with the former having higher priority. If any such files are found, the rules / filetypes defined in those files override the default rules / filetypes defined in `src/classifier/config`. This allows industry rule and filetype config to be updated without re-writing code and redeploying.

In the current implementation, however, overriding the default config would cause some issues:
1) Whenever we add a new supported document class, we'd need to retrain our classifier. However, this wouldn't necessitate redeployment if we hosted our logistic regression classifier externally (e.g., in blob storage), and our choice of classifier means adding new document classes doesn't require expensive fine-tuning with large amounts of high quality data.
2) Updating the supported document types would necessitate a code change and redeployment, as the text extraction logic in `extract.py` would need to be updated to support the new document type. This could potentially be addressed by using a more comprehensive, umbrella text extraction algorithm that supports a wide variety of filetypes.

### Areas for further improvement:
This is a highly open-ended challenge with enough scope to easily spend days, or even weeks, on. As such, the pipeline I've created can be improved in virtually every facet. Some suggestions for new features and improvements include, but are by no means limited to:

- Adding comprehensive logging for in-depth classification analysis, allowing assessment of misclassifications, confusion clusters, etc.
- Improving error handling — adding comprehensive try / except blocks and a global error handler. The current pipeline is quite fragile and relies on Flask's built-in error handler. For example, currently, corrupted, encrypted, or unreadable files result in unhandled errors during content extraction, causing Flask to return a default 5xx response. Ideally, these should return a 4xx error, with custom logic to handle the issue gracefully.
- Adding typehints to the code to improve clarity and show intent, enforcing types at compile / runtime with libraries such as mypy and typeguard.
- Improving the confidence scoring mechanism — the current approach oversimplifies confidence by directly translating scores from different classification methods into a single confidence value. For example, a fuzzy match score of 85 and a classifier prediction probability of 0.85 are treated as equivalent, even though they represent fundamentally different things. A more sophisticated method for estimating confidence should be implemented, or alternatively, the system should clearly communicate to the client what each score actually represents.
- Adding a criticality field to requests that indicates how important accurate classification of the document is. For critical documents, we could modify behaviour such that the system continues through the full pipeline even after an initial match.
- Potentially adding an ML-based classification step based on the filename — for example, using an OpenAI call with a classification prompt and the filename (which we assume contains no sensitive information) at some point in the pipeline.
- More comprehensive testing — unit, integration and E2E, with a variety of edge cases and real-world documents.
- Creating better training data for our models either by using text extracted from real-world documents or increasing the sophistication of our synthetic data generators.
- Offloading expensive tasks such as OCR to a worker queue — decouples such processes from the req-res cycle to keep the API responsive and scalable.

### LLM disclaimer:
In the interest of time, I used LLMs in specific parts of the project to help speed things up, specifically with sections that 1) I'm less practised in or 2) are time-consuming and not integral to the core pipeline logic. Four areas fell into one or both of these categories:
1) Creating example rules for each industry (`industry_rules.yaml`).
2) Creating scripts for generating synthetic data.
3) Building test cases in test files.
4) Creating the script for building the classifier and picking appropriate hyperparameters.
