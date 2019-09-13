<!--[![Build Status](https://travis-ci.org/obophenotype/upheno-dev.svg?branch=master)](https://travis-ci.org/obophenotype/upheno-dev)
[![DOI](https://zenodo.org/badge/13996/obophenotype/upheno-dev.svg)](https://zenodo.org/badge/latestdoi/13996/obophenotype/upheno-dev)
-->
# Framework for the automated construction of uPheno 2.0 (alpha)

uPheno 2.0, due December 2019, will be the new version of the Unified Phenotype Ontology ([uPheno](https://github.com/obophenotype/upheno)). 

The uPheno project aims to unify the annotation of phenotypes across species in a manner analogous to unification of gene function annotation by the Gene Ontology. uPheno 2.0 builds on earlier efforts with a new strategy that directly leverages the work of the phenotype ontology development community and incorporates phenotypes from a much wider range of species. We have organised a [collaborative community effort](https://github.com/obophenotype/upheno/wiki/Phenotype-Ontologies-Reconciliation-Effort), including representatives of all major model organism databases, to document and align [formal design patterns](https://github.com/obophenotype/upheno/tree/master/src/patterns) for representing phenotypes and further develop reference ontologies, such as PATO, which are used in these patterns.  A common development infrastructure makes it easy to use these design patterns to generate both species-specific ontologies and a species-independent layer that subsumes them. 

The resulting community-curated ontology for the representation and integration of phenotypes across species serves two general purposes:  
- Providing a community-developed framework for ontology editors to bootstrap, maintain and extend their phenotype ontologies in a scalable and standardised manner.  
- Facilitating the retrieval and comparative analysis of species-specific phenotypes through a deep layer of species-independent phenotypes.

## Architecture

UPheno 2.0 comprises three layers. The phenotype base layer contains the phenotype terms defined by the various organism-specific communities, such as C. elegans and Human. The reference ontology layer contains the subsets of external ontologies that are referenced by the base layer such as GO, Chebi and UBERON. The Upheno integration layer is generated automatically from the base layer and the reference ontology layer and contains species independent phenotype terms such as ‘abnormal skin morphology’.

## Contact

Please use this GitHub repository's [Issue tracker](https://github.com/obophenotype/upheno-dev/issues) to report errors or specific concerns related to the ontology. This pipeline is being developed by members of the Monarch Initiative.

## Acknowledgements

This ontology repository was created using the [ontology development kit](https://github.com/INCATools/ontology-development-kit).
