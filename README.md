# Cancer-Alterome
In the quest to unravel the intricate mechanisms underlying tumors, understanding cancer is crucial for developing effective treatments. In this project, Cancer-Alterome, addresses this challenge by presenting a literature-mined dataset focusing on the regulatory events within an organism's biological processes or clinical phenotypes induced by genetic alterations.  

The repository includes the complete pipeline implementation for the Cancer-Alterome construction, basically used to extract the `Genetic Alteration caused Regulatory Events` (`GARE`), as well as the script for generating the data visualization in MS.

- - -

## Environment Configuration

### Python Version
This project is developed using Python 3.6+.

### Python Libraries
The Pipeline implementation relies on the underlying python library, e.g. numpy, scipy, nltk, Pyecharts.
You can install these library via `pip install <library>` or `conda install <library>`.

___

## External Tools
The pipeline implementation involves several external tools, the description and links of these tools are provided below. Users may need to configure and test these tools before running the full Cancer-Alterome pipeline.


- [**PubTator Central**](https://www.ncbi.nlm.nih.gov/research/pubtator/): This tool are used to identify and standardize genes, point mutations, single nucleotide mutations, and disease mentions in pipeline.
  
- [**AGAC-NER**](https://github.com/YaoXinZhi/BERT-CRF-for-BioNLP-OST2019-AGAC-Task1): This model are used to identify the genetic alteration and trigger word defined in AGAC corpus.
  
- [**AGAC-RE**](https://github.com/YaoXinZhi/BERT-for-BioNLP-OST2019-AGAC-Task2): This model are used to identify the genetic alteration and trigger word defined in AGAC corpus.

  
- [**OGER++**](https://pub.cl.uzh.ch/purl/OGER): This model are used to extract the relations defined in AGAC corpus, include \textit{Theme} and \textit{Cause}.

- [**PhenoTagger**](https://github.com/ncbi-nlp/PhenoTagger): This tool are used to identify the mentions of GO concepts in the text, and normalize mentions to GO IDs.

---
## Pipeline Usage
All `16 backbone scripts` for each step in pipeline are released in this repository, and the script names are `numbered` indicating the `running order`. The usages of the script are listed below.


### 1. Literature Preparation
The `LiteraturePrepare` folder contains 5 scripts.

- `1. get_pmc_pmid.py` and `1.1 esearch_get_pmc_pmid.py` is used to search PubMed and PubMed Central databases based on keywords and to download PMID and PMCID.

- `2. pmc_pmid_to_biocjson.py` is used to automatically download the abstracts as well as full text of the corresponding literature from PubMed Central's API based on the PMIDs and PMCIDs obtained in the previous step, and includes the PubTator annotation.

- `3. biocjson_to_pubtator.py` provides PubTator format conversion of BiocJson format files. This conversion step is necessary due to the pipeline design where the PubTator format is used for subsequent data processing.
 
- `4. biocjson_to_jounral_info.py` is used to extract the journal information of the article from the BiocJson format file, e.g. journal name, the year of publication.

### 2. Named Entity Recognition and Normalization.
The `NamedEntityRecognization` folder contains 6 scripts with the following usage guidelines.  

It should be noted that since [**AGAC-NER**](https://github.com/YaoXinZhi/BERT-CRF-for-BioNLP-OST2019-AGAC-Task1) already have independent repositories, only the format conversion scripts for they input and output are provided here.

In addition, before using [**OGER++**](https://pub.cl.uzh.ch/purl/OGER) and [**PhenoTagger**](https://github.com/ncbi-nlp/PhenoTagger), you may need to visit their project websites and configure the tool environment.


- `1. pubtator_to_agac_ner_input.py` provides the conversion of PubTator format documentation to AGAC-NER model input format.
  
- `2. agac_ner_output_procss.py` provides formatting of AGAC-NER model output documents.
  
- `3. oger_tagger.py` provides batch GO concept annotation for OGER++. the vocabularies required for OGER++ are provided in go.term.tsv and hpo.term.tsv.
  
- `4. OGER_result_process.py` provides the result processing for OGER++.
  
- `5. PhenoTagger_training.py` provides the training function of PhenoTagger.
   
- `6. PhenoTagger_tagging.py` provides batch tagging of HPO concepts by PhenoTagger.  


### 3. Relation Extraction
In the `RelationExtraction` folder, 2 scripts are provided with the following usages.
Similarly, you can find the usages for [**AGAC-RE**](https://github.com/YaoXinZhi/BERT-for-BioNLP-OST2019-AGAC-Task2) in it's repositories.

- `1. ner_tagging_to_agac_re_input.py` provides the format conversion of the AGAC-NER output to the AGAC-RE inputs. 
  
- `2. agac_re_infer_process.py` is used to process the prediction results of AGAC-RE.


### 4. Regulatory Events Identification
The `GARE-Extraction` folder contains one script.

- `1. rule_based_gare_extraction.py` is used to extract the complete GARE from the above steps based on the design rules of GARE.


### 5. Data Visualization
The `DatabasePrepare` folder contains 3 scripts for data format conversion and visualization.

- `1. gare_to_database.py` is used to convert the GARE results generated in the previous step into a more readable tab-delimited database format.

- `2. multi-gene-heatmap.ipynb` is used to plot the heatmap web page visualization shown in the literature.

- `3. Signle_gene_SanKey.ipynb` is used to plot the SanKey web page visualization presented in the literature.

---

## Reference

[1] Wei, Chih-Hsuan, et al. "PubTator central: automated concept annotation for biomedical full text articles." Nucleic acids research 47.W1 (2019): W587-W593.  
[2] Wang, Yuxing, et al. "Guideline design of an active gene annotation corpus for the purpose of drug repurposing." 2018 11th International Congress on Image and Signal Processing, BioMedical Engineering and Informatics (CISP-BMEI). IEEE, 2018.  
[3] Wang, Yuxing, et al. "An overview of the active gene annotation corpus and the BioNLP OST 2019 AGAC track tasks." Proceedings of The 5th workshop on BioNLP open shared tasks. 2019.  
[4] Furrer, Lenz, et al. "OGER++: hybrid multi-type entity recognition." Journal of cheminformatics 11.1 (2019): 1-10.  
[5] Luo, Ling, et al. "PhenoTagger: a hybrid method for phenotype concept recognition using human phenotype ontology." Bioinformatics 37.13 (2021): 1884-1890.  



