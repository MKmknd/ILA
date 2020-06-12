

## How to get the result

### Extract commit messages info from the target repository

First, we need to extract all commit messages info (commit date etc.) from the target repository.

```Python
from preprocess.check_all_log_repository import ExtractCommitMessage
from Utils import util

ins = ExtractCommitMessage(repo_dir="{{ path to repository }}",
                           p_name="{{ repo name }}", apache_issue_id_prefix="{{ repo issue id prefix}}",
                           output_dir="{{ path to data output directory}}", verbose=1)
ins.run()
```

Then, you can get the result in {{ path to data output directory}}
as {{ repo name }}_log_message_info.pickle.

Please check tests/preprocess_check_all_log_repository.py for a  
concrete example.  

### Extract commit message with and without issue ids

Second, we need to extract commit messages with and without issue ids. 

```Python
from preprocess.extract_log_msg_repository import ExtractRawCommitMessage
from Utils import util

ins = ExtractRawCommitMessage(repo_dir="{{ path to repository }}",
                           p_name="{{ repo name }}", apache_issue_id_prefix="{{ repo issue id prefix}}",
                           output_dir="{{ path to data output directory}}")
ins.run()
```
Then, you can get the result in {{ path to data output directory}}
as {{ repo name }}_log_message_without_issueid.pickle and
{{ repo name }}_log_message.pickle


### Clone data

$ cd GS
$ git clone https://github.com/taxio/bouffier-java


### Download NLTK dataset

```Python
import nltk
try:
    nltk.find('tokenizers/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.find('tokenizers/wordnet')
except LookupError:
    nltk.download('wordnet')
```

### Try ILAs!
Now, we have done the preparation. We can execute any ILAs. 



## How to use ILAs?

You can find how to use each ILA to check tests/{{ ILA name }}_test.py.
Here, We write an additional description.

### Keyword Extraction (KE)

An example is the following:

```Python
from KE import keyword_extraction

ins = keyword_extraction.KeywordExtraction()
data = ins.run(hash_list, issue_id_list, "./../preprocess/data_AVRO/avro_log_message_info.pickle")
```

Here:
- hash_list: a list of all commit hashes that we want to study (e.g., ['abc123...', ...])
- issue_id_list: a list of issue report id list (e.g., ['AVRO-XXX', '..'...])
- The third argument is the log message info that we prepared in the previous section.
- The return value data is a dictionary. The key is an issue id; the value is a list of commit hashes that correspond to this issue id.

The return value data is the result of KE.

### Time Filtering (TF)

An example is the following:

```Python
from TF import time_filtering

ins = time_filtering.TimeFiltering()
data = ins.run(hash_list, issue_id_list, date_issue_dict, log_message_info_path)
```

Here:
- hash_list: a list of all commit hashes that we want to study (e.g., ['abc123...', ...])
- issue_id_list: a list of issue report id list (e.g., ['AVRO-XXX', '..'...])
- log_message_info_path: the pickle path of the log message info that we prepared in the previous section. (*_log_message_info.pickle)
- date_issue_dict: a dictionary of the issue report date information. The key is an issue id; the value is a dictionary: the key is the date information keywords (created, updated, and resolutiondate); the value is the datetime object for each date.
- The return value data is a dictionary. The key is an issue id; the value is a list of commit hashes that correspond to this issue id.

The return value data is the result of TF.

An example of date_issue_dict is the following:

```Python
date_issue_dict = {"TEST-1": {"created": datetime object (2020-6-20),
                              "updated": datetime object (2020-6-22) ,
                              "resolutiondate": datetime object (2020-6-25)},
                   "TEST-2": ...
                  }          
```

To check the details of the datetime object, please check:  
tests/TF_test.py's extract_datetime_from_string function.

### Text Similarity (TS)
