from resultados.services.megasena_importer import parse_html_megasena

HTML_FIXTURE = """
<html><body><table>
<tr><th>Concurso</th><th>Data</th><th>1ª</th><th>2ª</th><th>3ª</th><th>4ª</th><th>5ª</th><th>6ª</th></tr>
<tr><td>1</td><td>11/03/1996</td><td>41</td><td>05</td><td>04</td><td>52</td><td>30</td><td>33</td></tr>
<tr><td>2</td><td>18/03/1996</td><td>09</td><td>37</td><td>31</td><td>41</td><td>01</td><td>14</td></tr>
<tr><td>cabeçalho qualquer não-numérico</td><td>linha sem data</td></tr>
<tr><td>2731</td><td>01/06/2024</td><td>10</td><td>20</td><td>30</td><td>40</td><td>50</td><td>60</td></tr>
</table></body></html>
"""


def test_parse_html_extracts_three_results():
    res = parse_html_megasena(HTML_FIXTURE)
    assert len(res) == 3
    assert res[0].concurso == 1
    assert res[0].dezenas == (41, 5, 4, 52, 30, 33)
    assert res[2].concurso == 2731
    assert res[2].data.year == 2024
