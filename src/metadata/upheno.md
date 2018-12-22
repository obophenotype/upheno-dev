---
layout: ontology_detail
id: upheno
title: uPheno Dev
jobs:
  - id: https://travis-ci.org/obophenotype/upheno-dev
    type: travis-ci
build:
  checkout: git clone https://github.com/obophenotype/upheno-dev.git
  system: git
  path: "."
contact:
  email: cjmungall@lbl.gov
  label: Chris Mungall
description: uPheno Dev is an ontology...
domain: stuff
homepage: https://github.com/obophenotype/upheno-dev
products:
  - id: upheno.owl
  - id: upheno.obo
dependencies:
 - id: ro
 - id: pato
 - id: go
 - id: uberon
 - id: wbbt
 - id: plana
 - id: xao
 - id: zfa
tracker: https://github.com/obophenotype/upheno-dev/issues
license:
  url: http://creativecommons.org/licenses/by/3.0/
  label: CC-BY
---

Enter a detailed description of your ontology here
