# -*- coding: utf-8 -*-
"""
Utilitários para manipulação de strings
"""

import re
import unicodedata
from typing import List, Optional, Dict, Any

class StringUtils:
    """Utilitários para manipulação de strings"""
    
    @staticmethod
    def remover_acentos(texto: str) -> str:
        """Remove acentos de um texto mantendo a capitalização original"""
        if not texto:
            return ""
        return ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
    
    @staticmethod
    def normalizar_texto(texto: str) -> str:
        """Normaliza texto removendo acentos e convertendo para minúsculas"""
        if not texto:
            return ""
        
        # Remove acentos
        texto_normalizado = unicodedata.normalize('NFD', texto)
        texto_sem_acentos = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
        
        # Converte para minúsculas
        return texto_sem_acentos.lower()
    
    @staticmethod
    def limpar_espacos(texto: str) -> str:
        """Remove espaços extras e quebras de linha desnecessárias"""
        if not texto:
            return ""
        
        # Remove espaços no início e fim
        texto_limpo = texto.strip()
        
        # Substitui múltiplos espaços por um único espaço
        texto_limpo = re.sub(r'\s+', ' ', texto_limpo)
        
        return texto_limpo
    
    @staticmethod
    def capitalizar_nome(nome: str) -> str:
        """Capitaliza nomes próprios corretamente"""
        if not nome:
            return ""
        
        # Palavras que devem ficar em minúsculas
        preposicoes = {'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'na', 'no', 'nas', 'nos'}
        
        palavras = StringUtils.limpar_espacos(nome).lower().split()
        palavras_capitalizadas = []
        
        for i, palavra in enumerate(palavras):
            if i == 0 or palavra not in preposicoes:
                palavras_capitalizadas.append(palavra.capitalize())
            else:
                palavras_capitalizadas.append(palavra)
        
        return ' '.join(palavras_capitalizadas)
    
    @staticmethod
    def extrair_numeros(texto: str) -> str:
        """Extrai apenas números de uma string"""
        if not texto:
            return ""
        
        return re.sub(r'[^\d]', '', texto)
    
    @staticmethod
    def formatar_cpf(cpf: str) -> str:
        """Formata CPF com pontos e hífen"""
        numeros = StringUtils.extrair_numeros(cpf)
        
        if len(numeros) != 11:
            return cpf  # Retorna original se não tiver 11 dígitos
        
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
    
    @staticmethod
    def formatar_cnpj(cnpj: str) -> str:
        """Formata CNPJ com pontos, barra e hífen"""
        numeros = StringUtils.extrair_numeros(cnpj)
        
        if len(numeros) != 14:
            return cnpj  # Retorna original se não tiver 14 dígitos
        
        return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
    
    @staticmethod
    def formatar_telefone(telefone: str) -> str:
        """Formata telefone com parênteses e hífen"""
        numeros = StringUtils.extrair_numeros(telefone)
        
        if len(numeros) == 10:  # Telefone fixo
            return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
        elif len(numeros) == 11:  # Celular
            return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
        else:
            return telefone  # Retorna original se não estiver no formato esperado
    
    @staticmethod
    def truncar_texto(texto: str, tamanho_max: int, sufixo: str = "...") -> str:
        """Trunca texto se exceder o tamanho máximo"""
        if not texto or len(texto) <= tamanho_max:
            return texto
        
        return texto[:tamanho_max - len(sufixo)] + sufixo
    
    @staticmethod
    def gerar_slug(texto: str) -> str:
        """Gera um slug a partir de um texto"""
        if not texto:
            return ""
        
        # Normaliza e remove acentos
        slug = StringUtils.normalizar_texto(texto)
        
        # Remove caracteres especiais, mantém apenas letras, números e espaços
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        
        # Substitui espaços e múltiplos hífens por um único hífen
        slug = re.sub(r'[\s-]+', '-', slug)
        
        # Remove hífens do início e fim
        slug = slug.strip('-')
        
        return slug
    
    @staticmethod
    def contar_palavras(texto: str) -> int:
        """Conta o número de palavras em um texto"""
        if not texto:
            return 0
        
        palavras = StringUtils.limpar_espacos(texto).split()
        return len(palavras)
    
    @staticmethod
    def buscar_texto_flexivel(texto_busca: str, texto_alvo: str) -> bool:
        """Busca texto de forma flexível (sem acentos, case insensitive)"""
        if not texto_busca or not texto_alvo:
            return False
        
        busca_normalizada = StringUtils.normalizar_texto(texto_busca)
        alvo_normalizado = StringUtils.normalizar_texto(texto_alvo)
        
        return busca_normalizada in alvo_normalizado
    
    @staticmethod
    def destacar_termo_busca(texto: str, termo_busca: str, 
                           tag_inicio: str = "<mark>", tag_fim: str = "</mark>") -> str:
        """Destaca termo de busca no texto"""
        if not texto or not termo_busca:
            return texto
        
        # Busca case insensitive
        padrao = re.compile(re.escape(termo_busca), re.IGNORECASE)
        return padrao.sub(f"{tag_inicio}\\g<0>{tag_fim}", texto)
    
    @staticmethod
    def extrair_iniciais(nome: str, max_iniciais: int = 3) -> str:
        """Extrai iniciais de um nome"""
        if not nome:
            return ""
        
        palavras = StringUtils.limpar_espacos(nome).split()
        iniciais = [palavra[0].upper() for palavra in palavras if palavra]
        
        return ''.join(iniciais[:max_iniciais])
    
    @staticmethod
    def formatar_valor_monetario(valor: float, simbolo: str = "R$", 
                               decimais: int = 2) -> str:
        """Formata valor monetário"""
        valor_formatado = f"{valor:,.{decimais}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"{simbolo} {valor_formatado}"
    
    @staticmethod
    def parse_valor_monetario(valor_str: str) -> Optional[float]:
        """Converte string monetária para float"""
        if not valor_str:
            return None
        
        # Remove símbolos monetários e espaços
        valor_limpo = re.sub(r'[R$\s]', '', valor_str.strip())
        
        # Substitui vírgula por ponto para decimais
        valor_limpo = valor_limpo.replace(',', '.')
        
        try:
            return float(valor_limpo)
        except ValueError:
            return None
    
    @staticmethod
    def gerar_lista_sugestoes(termo: str, opcoes: List[str], max_sugestoes: int = 10) -> List[str]:
        """Gera lista de sugestões baseada em um termo de busca"""
        if not termo or not opcoes:
            return []
        
        termo_normalizado = StringUtils.normalizar_texto(termo)
        sugestoes = []
        
        # Primeiro, adiciona correspondências exatas (início da palavra)
        for opcao in opcoes:
            opcao_normalizada = StringUtils.normalizar_texto(opcao)
            if opcao_normalizada.startswith(termo_normalizado):
                sugestoes.append(opcao)
        
        # Depois, adiciona correspondências parciais
        for opcao in opcoes:
            if opcao not in sugestoes:  # Evita duplicatas
                opcao_normalizada = StringUtils.normalizar_texto(opcao)
                if termo_normalizado in opcao_normalizada:
                    sugestoes.append(opcao)
        
        return sugestoes[:max_sugestoes]
    
    @staticmethod
    def validar_caracteres_especiais(texto: str, permitidos: str = "") -> bool:
        """Valida se o texto contém apenas caracteres permitidos"""
        if not texto:
            return True
        
        # Caracteres básicos sempre permitidos
        basicos = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
        acentuados = "áàâãäéèêëíìîïóòôõöúùûüçñÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ"
        
        caracteres_validos = basicos + acentuados + permitidos
        
        for char in texto:
            if char not in caracteres_validos:
                return False
        
        return True
    
    @staticmethod
    def converter_para_ascii(texto: str) -> str:
        """Converte texto para ASCII removendo acentos"""
        if not texto:
            return ""
        
        # Normaliza e remove acentos
        texto_normalizado = unicodedata.normalize('NFD', texto)
        texto_ascii = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
        
        # Remove caracteres não-ASCII restantes
        texto_ascii = texto_ascii.encode('ascii', 'ignore').decode('ascii')
        
        return texto_ascii
    
    @staticmethod
    def formatar_lista_para_texto(lista: List[str], separador: str = ", ", 
                                 ultimo_separador: str = " e ") -> str:
        """Formata lista para texto legível"""
        if not lista:
            return ""
        
        if len(lista) == 1:
            return lista[0]
        
        if len(lista) == 2:
            return f"{lista[0]}{ultimo_separador}{lista[1]}"
        
        return f"{separador.join(lista[:-1])}{ultimo_separador}{lista[-1]}"
    
    @staticmethod
    def obter_extensao_arquivo(nome_arquivo: str) -> str:
        """Obtém a extensão de um arquivo"""
        if not nome_arquivo or '.' not in nome_arquivo:
            return ""
        
        return nome_arquivo.split('.')[-1].lower()
    
    @staticmethod
    def gerar_nome_arquivo_seguro(nome_original: str) -> str:
        """Gera nome de arquivo seguro removendo caracteres problemáticos"""
        if not nome_original:
            return "arquivo"
        
        # Remove acentos e converte para minúsculas
        nome_limpo = StringUtils.normalizar_texto(nome_original)
        
        # Remove caracteres especiais, mantém apenas letras, números, pontos e hífens
        nome_limpo = re.sub(r'[^a-z0-9.-]', '_', nome_limpo)
        
        # Remove múltiplos underscores
        nome_limpo = re.sub(r'_+', '_', nome_limpo)
        
        # Remove underscores do início e fim
        nome_limpo = nome_limpo.strip('_')
        
        return nome_limpo if nome_limpo else "arquivo"