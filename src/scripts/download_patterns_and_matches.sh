TGT=matches2020-10-15

mkdir -p $TGT $TGT/patterns
cd $TGT
#wget --recursive -nH --no-parent https://data.monarchinitiative.org/upheno2/current/pattern-matches/
cp /Users/matentzn/ws/upheno/src/patterns/dosdp-dev/*.yaml patterns
cp /Users/matentzn/ws/upheno/src/patterns/dosdp-patterns/*.yaml patterns