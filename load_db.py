from langchain.document_loaders import DirectoryLoader, UnstructuredPowerPointLoader, YoutubeLoader
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from itertools import chain

persist_directory = 'db'
openai_api_key = ""
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

# Load all the slides
loader = DirectoryLoader(path='./slides/', glob="./*.pptx", loader_cls=UnstructuredPowerPointLoader)
docs_slides = loader.load()

# Get all the video ids
filename = 'video_ids.txt'
file = open(filename,'r')
video_ids = [id.strip('\n') for id in file.readlines()]

# Create a list of Youtube loaders based on video ids
loaders = [YoutubeLoader(id) for id in video_ids]

# Load the documents and split the docuemnts into smaller chunks for retrieval (similar to the length of the slides
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=100)
docs_vids = [loader.load_and_split(text_splitter) for loader in loaders]

# Unpack nested list
docs_vids = list(chain.from_iterable(docs_vids))

# Clean documents
for i in range(len(docs_vids)):
    docs_vids[i].page_content = (docs_vids[i].page_content).replace("\n", " ").replace("\xa0", "").replace("\ufeff", "").replace("  ", " ")
    docs_vids[i].page_content = (docs_vids[i].page_content).replace("[music fades out]", "").replace("[Music, laughing]", "").replace("[Music]", "").replace("[synth music]", "")
    docs_vids[i].page_content = (docs_vids[i].page_content).replace("[Loud, electronic music]", "").replace("[pause]", "").replace("[music]", "").replace("[swish]", "")
    docs_vids[i].page_content = (docs_vids[i].page_content).replace("[ping pong sfx]", "").replace("[pop, pop]", "").replace("[pops]", "").replace("[Laughing]", "")
    docs_vids[i].page_content = (docs_vids[i].page_content).replace("[Typing sounds]", "").replace("[num]", "").replace("[Title: ", "").replace("[title: ", "")
    docs_vids[i].page_content = (docs_vids[i].page_content).replace("]", "").replace("[Closed captioning: ", "").replace("  ", " ").replace("  ", " ")
    docs_vids[i].page_content = (docs_vids[i].page_content).replace("[APPLAUSE ", "").replace("[MUSIC PLAYING ", "").replace("[LAUGHTER ", "").replace("[CHEERS ", "")
    docs_vids[i].page_content = (docs_vids[i].page_content).replace("[SCREAMS. ", "").replace("[SNORE, ", "").replace("[SLAMS TABLE ", "")

# Combine documents
docs = docs_slides + docs_vids

# Create vector store
vs = Chroma.from_documents(documents=docs, embedding=embeddings, persist_directory=persist_directory)