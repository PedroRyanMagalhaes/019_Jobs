# Guia de Uso do Pytest

## 📋 Índice
- [Instalação](#instalação)
- [Comandos Básicos](#comandos-básicos)
- [Comandos Avançados](#comandos-avançados)
- [Opções Úteis](#opções-úteis)
- [Exemplos Práticos](#exemplos-práticos)

---

## 🔧 Instalação

```powershell
pip install pytest
```

---

## 🚀 Comandos Básicos

### Rodar todos os testes
```powershell
pytest src/test/unit_test/
```

### Rodar todos os testes com modo verbose (detalhado)
```powershell
pytest src/test/unit_test/ -v
```

### Rodar um teste específico
```powershell
pytest src/test/unit_test/test_lenovo.py
```

### Rodar e mostrar prints (output capturado)
```powershell
pytest src/test/unit_test/ -s
```

### Combinar verbose + prints
```powershell
pytest src/test/unit_test/ -v -s
```

---

## ⚡ Comandos Avançados

### Parar no primeiro erro
```powershell
pytest src/test/unit_test/ -x
```

### Parar após N falhas
```powershell
pytest src/test/unit_test/ --maxfail=3
```

### Rodar testes por nome/padrão
```powershell
# Rodar apenas testes que contenham "lenovo"
pytest src/test/unit_test/ -k "lenovo"

# Rodar testes de Lenovo e Dell
pytest src/test/unit_test/ -k "lenovo or dell"

# Excluir testes específicos
pytest src/test/unit_test/ -k "not ciandt"
```

### Rodar último teste que falhou
```powershell
pytest src/test/unit_test/ --lf
```

### Rodar testes que falharam primeiro, depois os demais
```powershell
pytest src/test/unit_test/ --ff
```

---

## 🎯 Opções Úteis

### Traceback (rastreamento de erros)

```powershell
# Traceback curto (recomendado)
pytest src/test/unit_test/ --tb=short

# Traceback completo
pytest src/test/unit_test/ --tb=long

# Apenas uma linha por falha
pytest src/test/unit_test/ --tb=line

# Sem traceback
pytest src/test/unit_test/ --tb=no
```

### Duração dos testes

```powershell
# Mostrar os 3 testes mais lentos
pytest src/test/unit_test/ --durations=3

# Mostrar duração de todos
pytest src/test/unit_test/ --durations=0
```

### Modo quieto (menos verbose)

```powershell
pytest src/test/unit_test/ -q
```

### Mostrar variáveis locais em falhas

```powershell
pytest src/test/unit_test/ -l
```

---

## 📊 Relatórios e Análises

### Coletar testes sem executar
```powershell
pytest src/test/unit_test/ --collect-only
```

### Contar testes
```powershell
pytest src/test/unit_test/ --collect-only -q
```

### Gerar relatório HTML (requer pytest-html)
```powershell
pip install pytest-html
pytest src/test/unit_test/ --html=report.html
```

### Cobertura de código (requer pytest-cov)
```powershell
pip install pytest-cov
pytest src/test/unit_test/ --cov=src/scrapers
```

---

## 💡 Exemplos Práticos

### Exemplo 1: Teste rápido com saída limpa
```powershell
pytest src/test/unit_test/test_lenovo.py -v --tb=short
```

### Exemplo 2: Rodar todos, parar no primeiro erro
```powershell
pytest src/test/unit_test/ -x -v
```

### Exemplo 3: Rodar todos com prints e detalhes
```powershell
pytest src/test/unit_test/ -v -s --tb=short
```

### Exemplo 4: Rodar apenas testes de empresas específicas
```powershell
pytest src/test/unit_test/ -k "ambevtech or bosch or dell" -v
```

### Exemplo 5: Rodar todos menos um teste problemático
```powershell
pytest src/test/unit_test/ -k "not ciandt" -v
```

### Exemplo 6: Modo completo (para debugging)
```powershell
pytest src/test/unit_test/ -v -s -l --tb=long
```

### Exemplo 7: Modo silencioso (apenas resultados)
```powershell
pytest src/test/unit_test/ -q
```

---

## 🔍 Debugging com Pytest

### Entrar no debugger quando houver falha
```powershell
pytest src/test/unit_test/ --pdb
```

### Entrar no debugger logo no início de cada teste
```powershell
pytest src/test/unit_test/ --trace
```

---

## ⚙️ Configuração Personalizada

Você pode criar um arquivo `pytest.ini` na raiz do projeto:

```ini
[pytest]
# Opções padrão
addopts = -v --tb=short

# Padrão de arquivos de teste
python_files = test_*.py

# Padrão de funções de teste
python_functions = test_*

# Diretórios a ignorar
norecursedirs = .git .venv __pycache__
```

---

## 📝 Atalhos Úteis

| Comando | Descrição |
|---------|-----------|
| `pytest` | Roda todos os testes no diretório atual |
| `pytest -v` | Modo verbose (detalhado) |
| `pytest -s` | Mostra prints |
| `pytest -x` | Para no primeiro erro |
| `pytest -k "nome"` | Filtra por nome |
| `pytest --lf` | Último teste que falhou |
| `pytest --tb=short` | Traceback resumido |
| `pytest -q` | Modo quieto |
| `pytest -l` | Mostra variáveis locais |

---

## 🎓 Dicas

1. **Use `-v -s`** para ver output detalhado durante os testes
2. **Use `-x`** quando quiser parar no primeiro erro para economizar tempo
3. **Use `-k`** para rodar subconjuntos de testes
4. **Use `--tb=short`** para mensagens de erro mais legíveis
5. **Use `--lf`** para reexecutar apenas testes que falharam anteriormente

---

## 📚 Recursos Adicionais

- Documentação oficial: https://docs.pytest.org/
- Plugins úteis: https://docs.pytest.org/en/latest/reference/plugin_list.html
- Pytest-cov: https://pytest-cov.readthedocs.io/
- Pytest-html: https://pytest-html.readthedocs.io/
