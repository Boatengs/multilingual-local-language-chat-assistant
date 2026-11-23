set -e
mkdir -p probe/out/flores
curl -sSL -o /tmp/flores.tgz https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz
tar xzf /tmp/flores.tgz -C /tmp
ls /tmp/flores200_dataset | head
for l in eng_Latn twi_Latn aka_Latn ewe_Latn hau_Latn; do
  wc -l /tmp/flores200_dataset/devtest/$l.devtest >> probe/out/flores/counts.txt
  head -3 /tmp/flores200_dataset/devtest/$l.devtest > probe/out/flores/$l.head.txt
done
ls /tmp/flores200_dataset/devtest | grep -i -E "gaa|^ga" > probe/out/flores/ga_files.txt || echo "no Ga file" > probe/out/flores/ga_files.txt
cat /tmp/flores200_dataset/README* 2>/dev/null | head -40 > probe/out/flores/readme_head.txt || true
