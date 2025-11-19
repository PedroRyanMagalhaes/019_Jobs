# Funil Inteligente para classificação de vagas
import re

# Camada 1: Filtro de Palavras-Chave
TECH_KEYWORDS = [
    'Developer', 'Desenvolvedor', 'Software', 'Dados', 'Data Engineer', 'Data Scientist', 'Python', 'Engenheiro de Software', 'Programador', 'DevOps', 'Full Stack', 'Backend', 'Frontend', 'Machine Learning', 'IA', 'AI', 'Inteligência Artificial', 'Cientista de Dados', 'Analista de TI', 'Analista de Dados', 'TI', 'IT', 'Tecnologia da Informação', 'Tech Lead', 'Cloud', 'Infraestrutura de TI', 'Mobile', 'Web Developer', 'Java', 'C#', '.NET', 'Javascript', 'React', 'Node', 'SQL', 'Database', 'Arquiteto de Software', 'Scrum Master', 'Tester', 'QA Engineer', 'Quality Assurance', 'Suporte Técnico de TI', 'Technical Support', 'System Administrator', 'Administrador de Sistemas', 'Angular', 'AWS', 'Azure', 'DevSecOps', 'Salesforce Developer', 'SAP Developer', 'Databricks', 'Android Developer', 'iOS Developer', 'Go Developer', 'Kotlin', 'TypeScript', 'Drupal Developer', 'SharePoint Developer', 'Adobe Experience Manager', 'AEM', 'Cybersecurity', 'Security Engineer', 'BI Developer', 'Business Intelligence', 'Master Data', 'Platform Engineer'
]

NON_TECH_KEYWORDS = [
    'Motorista', 'Copeira', 'Vendedor', 'Auxiliar de Limpeza', 'Recepcionista', 'Estoquista', 'Repositor', 'Operador de Caixa', 'Serviços Gerais', 'Atendente', 'Cozinheiro', 'Garçom', 'Babá', 'Zelador', 'Porteiro', 'Portaria', 'Manutenção', 'Auxiliar Administrativo', 'Auxiliar de Escritório', 'Auxiliar de Produção', 'Auxiliar de Estoque', 'Auxiliar de Serviços Gerais', 'Auxiliar de Cozinha', 'Auxiliar de RH', 'Auxiliar de Compras', 'Auxiliar de Vendas', 'Auxiliar de Logística', 'Auxiliar de Almoxarifado', 'Operador de Manufatura', 'Operador de Produção', 'Operador COI', 'Controladoria', 'Advogado', 'Jurídico', 'Médico', 'Enfermeiro', 'Técnico de Segurança', 'Merchandising', 'Comprador', 'Assistente de Relacionamento', 'Coordenador Jurídico', 'Consultor de Remuneração', 'Estágio Técnico Administrativo', 'Estagiário de Atração', 'Gerente de Vendas', 'Engenheiro Viabilidade Obras', 'Engenheiro de Obras', 'Comunicação Interna', 'Recursos Humanos Generalista', 'Estágio Superior - Administrativo', 'Estágio Administrativo', 'Finanças', 'Marketing e Pricing', 'Marketing', 'Pricing', 'Analista de Comunicação', 'RH Generalista', 'Eng Plan Elétrico', 'Engenheiro Elétrico', 'Transmissão', 'Planejador de Energia', 'Energia', 'Educação Corporativa', 'Operações Financeiras', 'Engenheiro Telecom', 'Telecom', 'Agricultura', 'Precision Agriculture', 'Operadora Logística', 'Operador Logística', 'Logística',
    # Novas adições baseadas nos exemplos
    'Novos Negócios', 'Risco', 'Prevenção à Lavagem de Dinheiro', 'Risco Socioambiental', 'Crédito Rural', 'Cobrança', 'Analista de Negócios', 'Governança', 'Padrões de Engenharia', 'Crédito', 'Suprimentos', 'Inteligência Vendas', 'Inteligência de Vendas', 'Compras', 'Mobilidade', 'Eficiência de Custos', 'Farmácia', 'Performance', 'Regionais', 'Treinamento Comercial', 'Pré-Vendas', 'SDR', 'Outbound', 'Vendas Externas', 'Farmer', 'Executivo de Vendas', 'Especialista Compras', 'Especialista de Mobilidade'
]

def filtrar_por_palavras_chave(titulo):
    titulo_lower = titulo.lower()
    # Normalizar espaços extras e hífens para melhor comparação
    titulo_normalizado = re.sub(r'[-\s]+', ' ', titulo_lower).strip()
    
    # Verificar primeiro as palavras NON-TECH (mais específicas)
    for palavra in NON_TECH_KEYWORDS:
        palavra_lower = palavra.lower()
        palavra_normalizada = re.sub(r'[-\s]+', ' ', palavra_lower).strip()
        # Usar word boundary para evitar falsos positivos
        # Mas também permitir que encontre dentro de frases com hífens, vírgulas, etc
        pattern = r'\b' + re.escape(palavra_normalizada) + r'\b'
        if re.search(pattern, titulo_normalizado):
            return 'non-tech'
    
    # Verificar palavras TECH (mais específicas)
    for palavra in TECH_KEYWORDS:
        palavra_lower = palavra.lower()
        palavra_normalizada = re.sub(r'[-\s]+', ' ', palavra_lower).strip()
        pattern = r'\b' + re.escape(palavra_normalizada) + r'\b'
        if re.search(pattern, titulo_normalizado):
            return 'tech'
    
    return 'duvida'

# Camada 2: Agrupamento para IA

def agrupar_duvidas(titulos, batch_size=30):
    duvidas = [t for t in titulos if filtrar_por_palavras_chave(t) == 'duvida']
    for i in range(0, len(duvidas), batch_size):
        yield duvidas[i:i+batch_size]

# Camada 3: Funções para leitura e escrita no banco serão implementadas separadamente.
