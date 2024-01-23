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

### Python Libraries
The Pipeline implementation relies on the underlying python library, e.g. numpy, scipy, nltk.
You can install it via pip install <library> or conda install <library>.

___

## External Tools
The implementation of the Cancer-Alterome pipeline relies on several external tools, several of which already have mature github repositories or project home pages. We provide a quick jump below to help you understand how to get started with these tools.

- [**PubTator Central**](https://www.ncbi.nlm.nih.gov/research/pubtator/): Biomedical named entity recognition, e.g. gene, point mutation, SNP, disease. The identified and normalized gene, point mutation, SNP and disease are keeped in pipeline.
- [**AGAC-NER**](https://github.com/YaoXinZhi/BERT-CRF-for-BioNLP-OST2019-AGAC-Task1): Named entity recognition of entities defined in AGAC, e.g. gene, genetic alteration, trigger word, molecular process activate, cellular process activity. In pipeline, only keep the identified genetic alteration and trigger word in this step.
- [**AGAC-RE**](https://github.com/YaoXinZhi/BERT-for-BioNLP-OST2019-AGAC-Task2): Relation extraction for the relation defined in the AGAC, include ThemeOf and CauseOf.
- [**OGER++**](https://pub.cl.uzh.ch/purl/OGER): A hybrid NER-CR system for text mining in the biomedical domain, it's used to identify and normalize the Gene Ontlogy (GO) concepts in the pipeline.
- [**PhenoTagger**](https://github.com/ncbi-nlp/PhenoTagger): A hybrid method that combines dictionary and deep learning-based methods to recognize Human Phenotype Ontology (HPO) concepts in unstructured biomedical text, it's used to identify and normalize the HPO concepts in the pipeline.

---
## Pipeline Usage
The `Backbone Scripts` for each step in the Cancer-Alterome pipeline are provided in the corresponding folder, with usage guidelines as follows.

### 1. Literature Prepare
The `LiteraturePrepare` folder contains 5 scripts.

- `1. get_pmc_pmid.py` and `1.1 esearch_get_pmc_pmid.py` is used to search PubMed and PubMed Central databases based on keywords and to download PMID and PMCID.

- `2. pmc_pmid_to_biocjson.py` is used to automatically download the abstracts as well as full text of the corresponding literature from PubMed Central's API based on the PMIDs and PMCIDs obtained in the previous step, and includes the PubTator annotation.

- `3. biocjson_to_pubtator.py` provides PubTator format conversion of BiocJson format files. This conversion step is necessary due to the pipeline design where the PubTator format is used for subsequent data processing.
 
- `4. biocjson_to_jounral_info.py` is used to extract the journal information corresponding to the article from the BiocJson format file, including the journal name, the year of publication, and so on.

### 2. Named Entity Recognition and Normalization.
The `NamedEntityRecognization` folder contains 6 scripts with the following usage guidelines.  

It should be noted that since [**AGAC-NER**](https://github.com/YaoXinZhi/BERT-CRF-for-BioNLP-OST2019-AGAC-Task1) and [**AGAC-RE**](https://github.com/YaoXinZhi/BERT-for-BioNLP-OST2019-AGAC-Task2) already have independent repositories, only the format conversion scripts for they input and output are provided here.

In addition, before using [**OGER++**](https://pub.cl.uzh.ch/purl/OGER) and [**PhenoTagger**](https://github.com/ncbi-nlp/PhenoTagger), you may need to visit their project websites and configure the tool environment.


- `1. pubtator_to_agac_ner_input.py` provides the conversion of PubTator format documentation to AGAC-NER model input format.
  
- `2. agac_ner_output_procss.py` provides formatting of AGAC-NER model output documents.
  
- `3. oger_tagger.py` provides batch GO concept annotation for OGER++. the vocabularies required for OGER++ are provided in go.term.tsv and hpo.term.tsv.
  
- `4. OGER_result_process.py` provides the result processing for OGER++.
  
- `5. PhenoTagger_training.py` provides the training function of PhenoTagger.
   
- `6. PhenoTagger_tagging.py` provides batch tagging of HPO concepts by PhenoTagger.  



### 3. Relation Extraction

### 4. Regulatory Events Identification

### 5. Data Visualization



---

## Reference

[1] Wei, Chih-Hsuan, et al. "PubTator central: automated concept annotation for biomedical full text articles." Nucleic acids research 47.W1 (2019): W587-W593.  
[2] Wang, Yuxing, et al. "Guideline design of an active gene annotation corpus for the purpose of drug repurposing." 2018 11th International Congress on Image and Signal Processing, BioMedical Engineering and Informatics (CISP-BMEI). IEEE, 2018.  
[3] Wang, Yuxing, et al. "An overview of the active gene annotation corpus and the BioNLP OST 2019 AGAC track tasks." Proceedings of The 5th workshop on BioNLP open shared tasks. 2019.  
[4] Furrer, Lenz, et al. "OGER++: hybrid multi-type entity recognition." Journal of cheminformatics 11.1 (2019): 1-10.  
[5] Luo, Ling, et al. "PhenoTagger: a hybrid method for phenotype concept recognition using human phenotype ontology." Bioinformatics 37.13 (2021): 1884-1890.  



