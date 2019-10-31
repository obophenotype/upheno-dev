OBO=http://purl.obolibrary.org/obo
sh run.sh robot reason -I $OBO/xpo.owl --equivalent-classes-allowed none -o test.owl
sh run.sh robot reason -I $OBO/dpo.owl --equivalent-classes-allowed none -o test.owl
sh run.sh robot reason -I $OBO/mp.owl --equivalent-classes-allowed none -o test.owl
sh run.sh robot reason -I $OBO/hp.owl --equivalent-classes-allowed none -o test.owl
sh run.sh robot reason -I $OBO/wbphenotype.owl --equivalent-classes-allowed none -o test.owl
