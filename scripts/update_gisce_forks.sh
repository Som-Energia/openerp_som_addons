#!/bin/bash
echo "Start sync repos"
date
gh repo sync Som-Energia/erp -b developer
gh repo sync Som-Energia/poweremail -b v5_backport
gh repo sync Som-Energia/webclient -b main
gh repo sync Som-Energia/oorq -b api_v5
gh repo sync Som-Energia/lleida_net_api -b master
gh repo sync Som-Energia/gestionatr -b master
gh repo sync Som-Energia/destral -b master
gh repo sync Som-Energia/poweremail-modules -b master
gh repo sync Som-Energia/libFacturacioATR -b master
gh repo sync Som-Energia/powerprofile -b master
gh repo sync Som-Energia/mongodb_backend -b gisce
echo "End sync repos"
echo "=============================="

# Discontinued forks, our repo is ahead than forked
#gh repo sync Som-Energia/heman -b master
