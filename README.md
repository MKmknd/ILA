
## Clone

$ cd GS
$ git clone https://github.com/taxio/bouffier-java


## How to get the result

### Extract commit messages from the target repository

First, we need to extract all commit messages from the target repository.

```
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



