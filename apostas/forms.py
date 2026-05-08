from django import forms

from .models import TipoJogo


class FiltroComprovanteForm(forms.Form):
    data_inicio = forms.DateField(
        required=False,
        label="Data inicial",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    data_fim = forms.DateField(
        required=False,
        label="Data final",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    tipo_jogo = forms.ModelChoiceField(
        required=False,
        queryset=TipoJogo.objects.all().order_by("nome"),
        to_field_name="slug",
        label="Tipo de jogo",
        empty_label="Todos",
    )
