#!/bin/bash

# Generates the report of the previous month unless you provide an isodate
# in that case generate sthe report of the month containing the date.



die() {
    [ -z "$1" ] || echo -e '\033[34;1mError: '$*'\033[0m' >&2
    emili.py \
        --subject "ERROR: Informe cambios de comercializador, $year-$month" \
        --to itcrowd@somenergia.coop \
        --to atr@somenergia.coop \
        --from sistemes@somenergia.coop \
        --config $scriptpath/dbconfig.py \
        --format md \
        --style somenergia.css \
        --body "$*" \

    exit -1
}
step() {
    echo -e '\033[34;1m:: '$*'\033[0m'
}

scriptpath=$(dirname $(readlink -f "$0"))
cd "$scriptpath"
 

today=$(date -I)
IFS='-' read -r year month day <<< "$today" # split date
lastMonthEnd=$(date -I -d "$year-$month-01 - 1 day") # last day of last month
IFS='-' read -r year month day <<< "${1:-$lastMonthEnd}" # split date

step "Generant resum del $year-$month-$day"

python cron_informe_cnmc_canvi_comer.py $year $month 1

allreports=(/tmp/SI_R2-???_E_${year}${month}_??.xml)
csvreports=(/tmp/SI_R2-???_E_${year}${month}_??.csv)
step "allreports: $allreports"
lastReport=${allreports[*]: -1}
step "lastReport: $lastReport"

MONTHS=("" Enero Febrero Marzo Abril Mayo Junio Julio Agosto Septiembre Octubre Noviembre Diciembre)

monthname=${MONTHS[$((10#$month))]}


step "Enviant resultats..."

TEXTOK="
# Informe de Cambios de comercializadora para SomEnergia $monthname de $year
Les adjuntamos el informe de cambios de comercializador correspondiente al
mes de ${MONTHS[$((10#$month))]} de $year para la comercializadora \"Som Energia SCCL\".
Un saludo.
"

emili.py \
    --subject "SomEnergia SCCL, informe cambios de comercializador, $year-$month" \
    --to atr@somenergia.coop \
    --to itcrowd@somenergia.coop \
    --from sistemes@somenergia.coop \
    --replyto itcrowd@somenergia.coop \
    --config $scriptpath/dbconfig.py \
    --format md \
    --style somenergia.css \
    $lastReport \
    $csvreports \
    --body "$TEXTOK" \
    || die "Error enviant fitxers CSV als companys"


emili.py \
    --subject "SomEnergia SCCL, informe cambios de comercializador, $year-$month" \
    --to cambiodecomercializador@cnmc.es \
    --bcc itcrowd@somenergia.coop \
    --from atr@somenergia.coop \
    --replyto atr@somenergia.coop \
    --config $scriptpath/dbconfig.py \
    --format md \
    --style somenergia.css \
    $lastReport \
    --body "$TEXTOK" \
    || die "Error enviant missatge a la CNMC"
