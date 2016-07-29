#!/usr/bin/env bash

if python3.5 gng/gng.py --update; then
	filebase=`date "+%Y%m%d-%H%M"`
	if python3.5 gng/gng.py --dump-list ${filebase}.tmp; then
		head -n 1 ${filebase}.tmp > ${filebase}.csv
		(sed '1d' ${filebase}.tmp | sort -t ',' -k '4,4r' -k '1,1d' -k '3,3f') >> ${filebase}.csv
		rm ${filebase}.tmp
	fi
fi
