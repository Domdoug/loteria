import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django  # noqa: E402

django.setup()

from django.db.models import Count, Sum  # noqa: E402

from apostas.models import Aposta, Comprovante  # noqa: E402
from importacao.models import ArquivoImportado  # noqa: E402

print("Total arquivos:", ArquivoImportado.objects.count())
print("Por status:")
for row in (
    ArquivoImportado.objects.values("status_importacao")
    .annotate(c=Count("id"))
    .order_by("status_importacao")
):
    print(f"  {row['status_importacao']}: {row['c']}")

print()
print("Top motivos de falha:")
motivos: Counter[str] = Counter()
for arq in ArquivoImportado.objects.filter(status_importacao="falha"):
    motivos[arq.mensagem_erro[:80]] += 1
for m, n in motivos.most_common(5):
    print(f"  {n}x: {m}")

print()
print("Total comprovantes:", Comprovante.objects.count())
print("Total apostas:", Aposta.objects.count())
total = Aposta.objects.aggregate(s=Sum("valor_aposta"))["s"]
print(f"Total geral apostado: R$ {total}")

print()
print("Comprovantes por tipo de jogo:")
for row in (
    Comprovante.objects.values("tipo_jogo__nome")
    .annotate(c=Count("id"), tot=Sum("valor_total_aposta"))
    .order_by("-tot")
):
    print(f"  {row['tipo_jogo__nome']}: {row['c']} comprovantes, R$ {row['tot']}")
