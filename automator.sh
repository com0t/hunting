#!/bin/bash

if [[ "$#" -lt 1 ]]; then
	echo "Use: $0 scope.txt"
	exit 1
fi

out_folder='subdomain'

if [[ ! -d $out_folder ]]; then
	mkdir $out_folder
fi

cat $1 | while read domain; do
	subfinder -d $domain | httprobe -c 200 | tee $out_folder/$domain
done

# automator CORS
cat $1 | while read domain; do
	python3 ~/git/hunting/cors.py -i $out_folder/$domain -t 400 -p 127.0.0.1:8080 | tee cors.out
done

# automator subd-takeover
cat $1 | while read domain; do
	python3 ~/git/hunting/subd-takeover.py -i $out_folder/$domain -t 300 | tee subd.out
done
