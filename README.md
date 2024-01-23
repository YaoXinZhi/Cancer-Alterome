# Cancer-Alterome
In the quest to unravel the intricate mechanisms underlying tumors, understanding cancer is crucial for developing effective treatments. Our project, Cancer-Alterome, addresses this challenge by presenting a literature-mined dataset focusing on the regulatory events within an organism's biological processes or clinical phenotypes induced by genetic alterations.  

The repository includes the original pipeline implementation for the Cancer-Alterome construction, as well as the code of data statistics and visualization.

- - -

## Environment Configuration

### Python Version
This project is developed using Python 3.6+.

### Virtual Environment
You can build a virtual environment for project operation.  
```
# Building a virtual environment
pip3 install virtualenv
pip3 install virtualenvwrapper

virtualenv -p /usr/local/bin/python3.6 $env_name --clear  

# active venv.
source $env_name/bin/activate  

# deactive venv.
deactivate
```

### Requirements

```
pip3 install -r requirements.txt
```
If you cannot download torch automatically through requirements.txt, you can delete the torch version information and get the command line of torch installation from the [torch official website](https://pytorch.org/). Note that the installed torch version needs to be the same as that in requirenemts.txt.


### Python Libraries
The Pipeline implementation relies on the underlying python library, e.g. numpy, scipy, nltk.
You can install it via pip install <library> or conda install <library>.

___

## External Tools
The implementation of the Cancer-Alterome pipeline relies on several external tools, several of which already have mature github repositories or project home pages. We provide a quick jump below to help you understand how to get started with these tools.

- [**PubTator Central**]([www.baidu.com](https://www.ncbi.nlm.nih.gov/research/pubtator/)): Biomedical named entity recognition, e.g. gene, point mutation, SNP, disease. 
- [**AGAC-NER**](https://github.com/YaoXinZhi/BERT-CRF-for-BioNLP-OST2019-AGAC-Task1): Named entity recognition of entities defined in AGAC, e.g. gene, genetic alteration, trigger word, molecular process activate, cellular process activity.
- [**AGAC-RE**](https://github.com/YaoXinZhi/BERT-for-BioNLP-OST2019-AGAC-Task2): Relation extraction for the relation defined in the AGAC, include ThemeOf and CauseOf.
- [**OGER**](https://pub.cl.uzh.ch/purl/OGER):A hybrid NER-CR system for text mining in the biomedical domain, it's used to identify and normalize the Gene Ontlogy (GO) concepts in the pipeline.
- [**PhenoTagger**]




--


