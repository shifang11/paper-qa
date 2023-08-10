from langchain.prompts import PromptTemplate

summary_prompt = PromptTemplate(
    input_variables=["text", "citation", "question", "summary_length"],
    template="Summarize the text below to help answer a question. "
    "Do not directly answer the question, instead summarize "
    "to give evidence to help answer the question. "
    'Reply "Not applicable" if text is irrelevant. '
    "Use {summary_length}. At the end of your response, provide a score from 1-10 on a newline "
    "indicating relevance to question. Do not explain your score. "
    "\n\n"
    "{text}\n\n"
    "Excerpt from {citation}\n"
    "Question: {question}\n"
    "Relevant Information Summary:",
)

qa_prompt = PromptTemplate(
    input_variables=["context", "answer_length", "question"],
    template="Provided context: {context}\n"
    "Write an answer ({answer_length}) "
    "Question: {question}\n"
    "Answer: ",
)

select_paper_prompt = PromptTemplate(
    input_variables=["question", "papers"],
    template="Select papers that may help answer the question below. "
    "Papers are listed as $KEY: $PAPER_INFO. "
    "Return a list of keys, separated by commas. "
    'Return "None", if no papers are applicable. '
    "Choose papers that are relevant, from reputable sources, and timely "
    "(if the question requires timely information). \n\n"
    "Question: {question}\n\n"
    "Papers: {papers}\n\n"
    "Selected keys:",
)

# We are unable to serialize with partial variables
# so TODO: update year next year
citation_prompt = PromptTemplate(
    input_variables=["text"],
    template="Provide the citation for the following text in MLA Format. The year is 2023\n"
    "{text}\n\n"
    "Citation:",
)

default_system_prompt = (
    "You are my game advisor. "
    "If the response in the Question section is not a question, no answer, "
    'only reply with "Feel free to ask any game-related Question". '
    "If the question is 1-3 words, no answer, "
    'only reply with "Please provide a more detailed description". '
    "If there is insufficient information, "
    'reply with "I cannot answer." and then provide a possible answer based on common sense in games. '
    "If the question contains Chinese, no answer, "
    'only reply with "Only supports English". '
    "Otherwise, you should write an answer (about 100 words) "
    "for the question below based on the provided context. "
    "Answer in an unbiased, comprehensive. "
    "If there are ambiguous terms or acronyms, first define them. "
)

