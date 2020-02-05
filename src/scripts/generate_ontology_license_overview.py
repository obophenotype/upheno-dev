#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 8 14:24:37 2018

@author: Nicolas Matentzoglu
"""

import os, sys
import yaml
from urllib.request import urlopen

obofoundry_listing = "http://obofoundry.org/registry/ontologies.yml"

data = urlopen(obofoundry_listing).read()
obo = yaml.load(data)

monarch_core_ontologies = ["mondo","hp","upheno","sepio","geno","ecto","maxo"]
monarch_key_ontologies = ["bfo","caro","chebi","cl","clo","eco","fao", "faldo","pco","xco","foaf","dc","oban","iao", "pw", "ero","fbbt","go","hsapdv","mondo","mpath","nbo","ncbitaxon","ncit","oba","pato","po","ro","so","stato","uberon","vt","wbbt","zfa"]

monarch_core_ontologies.sort()
monarch_key_ontologies.sort()

def get_markdown(oid, type="table"):
    global obo
    for o in obo['ontologies']:
        id = o['id']
        if id==oid:
            id_upper = id.upper()
            if 'title' in o: title = o['title']
            else: title = "NA"
            if 'license' in o: license = o['license']
            else: license = "NA"
            if 'label' in license: license_label = license['label']
            else: license_label = "NA"
            if 'logo' in license: license_logo = license['logo']
            else: license_logo = None
            if 'url' in license: license_url = license['url']
            else: license_url = "NA"
            if 'homepage' in o: homepage = o['homepage']
            else: homepage = "NA"
            if type=="table":
                if license_logo:
                    return "| [{}]({}) | <a href=\"{}\"><img src=\"{}\" alt=\"{}\" height=\"20\"></a> |".format(id_upper,homepage, license_url, license_logo, license_label)
                else:
                    return "| [{}]({}) | [{}]({}) |".format(id_upper, homepage, license_label, license_url)
            else:
                return "- [{}]({}): [{}]({})".format(id_upper, homepage, license_label, license_url)
    id_upper = oid.upper()
    if type == "table":
        return "| {} | Unknown |".format(id_upper)
    else:
        return "- {}: Unknown".format(id_upper)


markdown = []
markdown.append("| Ontology | License |")
markdown.append("| ---- | ----- |")
markdown.extend([get_markdown(i) for i in monarch_core_ontologies])
markdown.append("")
markdown.append("| Ontology | License |")
markdown.append("| ---- | ----- |")
markdown.extend([get_markdown(i) for i in monarch_key_ontologies])

for l in markdown:
    print(l)
