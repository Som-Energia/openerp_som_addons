#!/bin/bash

showsemanticcommands=0

verbose=false

step() { echo -e "\033[34;1m== "$@"\033[0m"; }
warn() { echo -e "\033[33m== "$@"\033[0m"; }
run() { $verbose && echo -e "\033[35;1m> "$@"\033[0m"; "$@"; }
skip() { $verbose && echo -e "\033[33;1mSkipped: > "$@"\033[0m"; }

INPUT_A="$1"
INPUT_B="$2"
OUTPUT="$3"

TMPDIR="$(mktemp -d)"
DIFFFOND=0

# Requires texlive-extra-utils poppler-utils

split() {
    # Receives a pdf and splits pages as vectorial (pdf) and raster (png)

    run pdfseparate "$1" "${2%png}pdf"
    #run pdftk  "$1"  burst  output "$2"

    run convert -scene 1 "$1" -fill white -opaque none +matte "$2"
}
rasterdiff() {
    # -alpha on: if not used, black is used as background and all letters blend
    # -compose src: default would be to output
    # colors are set to create a b/w mask instead a red on white image
    run compare -alpha on -metric AE "$a" "$b" \
        -compose Src \
        -highlight-color white \
        -lowlight-color black \
        PNG32:"$diff"
}
highlight() {
    # Receives a mask with the differences in white in a black bg
    # It draws a red outline and
    # sets a semi transparent white background to dimm the document
    run convert "$1" \
        -morphology Dilate Square:2 -negate -edge 3 \
        -channel rgb -fill "red" -opaque white \
        -channel rgba -fill "rgba(255,255,255,.4)" -opaque black \
        "$1"
}
overlay() {
    #run convert "$2" "$1" +swap -composite "$3"
    run pdfjam "$1" "$2" --outfile "$3" --nup "1x2" --noautoscale true --delta '0 -297mm' --papersize "{210mm,297mm}"
    #run pdftk "$2" background "$1" output "$3"
}
sidebyside() {
    run pdfjam -q "$1" "$2" --nup 2x1 --landscape -o "$3" 2> /dev/null
}
join() {
    run pdfjoin "${@:2}" -o "$1"
    #run pdftk "${@:2}" cat output "$1"
}
rasterjoin() {
	convert "${@:2}" "$1"
}

mkdir -p "${TMPDIR}/input_a"
mkdir -p "${TMPDIR}/input_b"
mkdir -p "${TMPDIR}/diff"
mkdir -p "${TMPDIR}/merged_a"
mkdir -p "${TMPDIR}/merged_b"
mkdir -p "${TMPDIR}/merged"

run split  "${INPUT_A}"  "${TMPDIR}/input_a/page_%03d.png"
run split  "${INPUT_B}"  "${TMPDIR}/input_b/page_%03d.png"

for page in ${TMPDIR}/input_a/page_*.png; do
    $verbose && step "Comparing $(basename $page .png)..."
    a="$page"
    b="${page/input_a/input_b}"

    apdf="${a/.png/.pdf}"
    bpdf="${b/.png/.pdf}"

    diff="${page/input_a/diff}"
    merged_a="${apdf/input_a/merged_a}"
    merged_b="${bpdf/input_b/merged_b}"
    merged="${apdf/input_a/merged}"

    run rasterdiff "$a" "$b" "$diff"
    error="$?"
    if [ "$error" != "0" ] ; then
        warn "Diff found ($error) in page $page"
        DIFFFOND=1
	else
		run rm "$diff"
    fi
done
if [ "$DIFFFOND" != "0" ]; then
	for page in ${TMPDIR}/input_a/page_*.png; do
		step "Processing $(basename $page .png)..."
		a="$page"
		b="${page/input_a/input_b}"

		apdf="${a/.png/.pdf}"
		bpdf="${b/.png/.pdf}"

		diff="${page/input_a/diff}"
		merged_a="${apdf/input_a/merged_a}"
		merged_b="${bpdf/input_b/merged_b}"
		merged="${apdf/input_a/merged}"

		if [ -e "$diff" ]; then
			run highlight "$diff" "$diff"
		else
			run convert label:Identicos "$diff"
		fi
		run overlay "$apdf" "$diff" "$merged_a"
		run overlay "$bpdf" "$diff" "$merged_b"
		run sidebyside "$merged_a" "$merged_b" "$merged"
	done
	run join "$OUTPUT" "${TMPDIR}"/merged/*.pdf
fi


skip run rm -rf "${TMPDIR}"

exit $DIFFFOND
