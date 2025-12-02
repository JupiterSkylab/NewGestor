from typing import List, Optional, Tuple
from datetime import datetime
from database.repositories import ProcessoRepository, LembreteRepository
from models.processo import Processo
import logging
from utils.intelligent_cache import get_intelligent_cache
from utils.structured_logger import get_logger, get_performance_logger, logged_method

class ProcessoService:
    """Service layer para operações com processos."""
    
    def __init__(self, processo_repo: ProcessoRepository, lembrete_repo: LembreteRepository):
        self.processo_repo = processo_repo
        self.lembrete_repo = lembrete_repo
        self.logger = get_logger("processo_service")
        self.perf_logger = get_performance_logger("processo_service")
        self._intelligent_cache = get_intelligent_cache()
        
    @logged_method("criar_processo", log_args=True, log_performance=True)
    def criar_processo(self, processo: Processo) -> Tuple[bool, str]:
        """Cria um novo processo com validações.
        
        Args:
            processo: Objeto Processo a ser criado.
            
        Returns:
            Tupla (sucesso, mensagem).
        """
        try:
            # Validações básicas
            if not processo.numero_processo:
                self.logger.warning(
                    "Tentativa de criar processo sem número",
                    extra_data={'processo_data': processo.__dict__}
                )
                return False, "Número do processo é obrigatório"
                
            if self.processo_repo.exists_by_numero(processo.numero_processo):
                self.logger.warning(
                    f"Tentativa de criar processo duplicado: {processo.numero_processo}",
                    extra_data={'processo_numero': processo.numero_processo}
                )
                return False, f"O processo '{processo.numero_processo}' já está cadastrado"
                
            # Define data de registro se não informada
            if not processo.data_registro:
                processo.data_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
            success = self.processo_repo.create(processo)
            if success:
                # Invalidar caches relacionados
                self._intelligent_cache.invalidate_processes()
                self._intelligent_cache.invalidate_statistics()
                self._intelligent_cache.invalidate_autocomplete()
                
                self.logger.info(
                    f"Processo criado com sucesso: {processo.numero_processo}",
                    extra_data={
                        'processo_numero': processo.numero_processo,
                        'secretaria': processo.secretaria,
                        'situacao': processo.situacao
                    }
                )
                return True, "Processo cadastrado com sucesso!"
            else:
                self.logger.error(
                    "Falha ao criar processo no repositório",
                    extra_data={'processo_numero': processo.numero_processo}
                )
                return False, "Erro ao cadastrar processo"
                
        except Exception as e:
            self.logger.error(
                f"Erro interno ao criar processo: {str(e)}",
                extra_data={'processo_numero': getattr(processo, 'numero_processo', 'N/A')}
            )
            return False, f"Erro ao cadastrar processo: {str(e)}"
            
    def atualizar_processo(self, processo: Processo, numero_original: str = None) -> Tuple[bool, str]:
        """Atualiza um processo existente.
        
        Args:
            processo: Objeto Processo com dados atualizados.
            numero_original: Número original do processo (para casos de alteração).
            
        Returns:
            Tupla (sucesso, mensagem).
        """
        try:
            if not processo.numero_processo:
                return False, "Número do processo é obrigatório"
                
            success = self.processo_repo.update(processo, numero_original)
            if success:
                # Invalidar caches relacionados
                self._intelligent_cache.invalidate_processes()
                self._intelligent_cache.invalidate_statistics()
                self._intelligent_cache.invalidate_autocomplete()
                
                self.logger.info(f"Processo {processo.numero_processo} atualizado com sucesso")
                return True, "Processo atualizado com sucesso!"
            else:
                return False, "Processo não encontrado ou erro na atualização"
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar processo: {e}")
            return False, f"Erro ao atualizar processo: {str(e)}"
            
    def excluir_processo(self, numero_processo: str) -> Tuple[bool, str]:
        """Exclui um processo (com backup).
        
        Args:
            numero_processo: Número do processo a ser excluído.
            
        Returns:
            Tupla (sucesso, mensagem).
        """
        try:
            if not numero_processo:
                return False, "Número do processo é obrigatório"
                
            success = self.processo_repo.delete_and_backup(numero_processo)
            if success:
                # Invalidar caches relacionados
                self._intelligent_cache.invalidate_processes()
                self._intelligent_cache.invalidate_statistics()
                self._intelligent_cache.invalidate_autocomplete()
                
                self.logger.info(f"Processo {numero_processo} excluído com sucesso")
                return True, f"Processo {numero_processo} excluído com sucesso!"
            else:
                return False, "Processo não encontrado"
                
        except Exception as e:
            self.logger.error(f"Erro ao excluir processo: {e}")
            return False, f"Erro ao excluir processo: {str(e)}"
            
    def buscar_processos(self, termo_busca: str = None, filtro_secretaria: str = None,
                        filtro_situacao: str = None, filtro_modalidade: str = None) -> List[Processo]:
        """Busca processos com filtros aplicados.
        
        Args:
            termo_busca: Termo de busca livre.
            filtro_secretaria: Filtro por secretaria.
            filtro_situacao: Filtro por situação.
            filtro_modalidade: Filtro por modalidade.
            
        Returns:
            Lista de processos encontrados.
        """
        try:
            return self.processo_repo.search_processos(
                termo_busca, filtro_secretaria, filtro_situacao, filtro_modalidade
            )
        except Exception as e:
            self.logger.error(f"Erro ao buscar processos: {e}")
            return []
            
    def listar_todos_processos(self) -> List[Processo]:
        """Lista todos os processos.
        
        Returns:
            Lista de todos os processos.
        """
        try:
            return self.processo_repo.get_all()
        except Exception as e:
            self.logger.error(f"Erro ao listar processos: {e}")
            return []
            
    def obter_processo(self, numero_processo: str) -> Optional[Processo]:
        """Obtém um processo pelo número.
        
        Args:
            numero_processo: Número do processo.
            
        Returns:
            Objeto Processo ou None se não encontrado.
        """
        try:
            return self.processo_repo.get_by_numero(numero_processo)
        except Exception as e:
            self.logger.error(f"Erro ao obter processo: {e}")
            return None
            
    def obter_nomes_autocomplete(self) -> List[str]:
        """Obtém nomes para autocompletar.
        
        Returns:
            Lista de nomes únicos.
        """
        try:
            return self.processo_repo.get_nomes_autocomplete()
        except Exception as e:
            self.logger.error(f"Erro ao obter nomes para autocomplete: {e}")
            return []
            
    def listar_trabalhos_excluidos(self) -> List[Tuple]:
        """Lista trabalhos excluídos para restauração.
        
        Returns:
            Lista de tuplas com dados dos trabalhos excluídos.
        """
        try:
            return self.processo_repo.get_trabalhos_excluidos()
        except Exception as e:
            self.logger.error(f"Erro ao listar trabalhos excluídos: {e}")
            return []
            
    def restaurar_processo(self, id_registro: int) -> Tuple[bool, str]:
        """Restaura um processo excluído.
        
        Args:
            id_registro: ID do registro no backup.
            
        Returns:
            Tupla (sucesso, mensagem).
        """
        try:
            success = self.processo_repo.restore_from_backup(id_registro)
            if success:
                return True, "Registro restaurado com sucesso!"
            else:
                return False, "Registro não encontrado no backup"
                
        except Exception as e:
            self.logger.error(f"Erro ao restaurar processo: {e}")
            return False, f"Erro ao restaurar processo: {str(e)}"
            
    def excluir_multiplos_processos(self, numeros_processos: List[str]) -> Tuple[int, int]:
        """Exclui múltiplos processos.
        
        Args:
            numeros_processos: Lista de números de processos a serem excluídos.
            
        Returns:
            Tupla (sucessos, falhas).
        """
        sucessos = 0
        falhas = 0
        
        for numero in numeros_processos:
            try:
                success = self.processo_repo.delete_and_backup(numero)
                if success:
                    sucessos += 1
                else:
                    falhas += 1
            except Exception as e:
                self.logger.error(f"Erro ao excluir processo {numero}: {e}")
                falhas += 1
                
        return sucessos, falhas
        
    def validar_dados_processo(self, processo: Processo) -> List[str]:
        """Valida os dados de um processo.
        
        Args:
            processo: Objeto Processo a ser validado.
            
        Returns:
            Lista de erros de validação (vazia se válido).
        """
        erros = []
        
        if not processo.numero_processo or not processo.numero_processo.strip():
            erros.append("Número do processo é obrigatório")
            
        if not processo.secretaria or not processo.secretaria.strip():
            erros.append("Secretaria é obrigatória")
            
        if not processo.situacao or not processo.situacao.strip():
            erros.append("Situação é obrigatória")
            
        # Validação de datas (formato básico)
        if processo.data_inicio:
            try:
                datetime.strptime(processo.data_inicio, '%Y-%m-%d')
            except ValueError:
                erros.append("Data de início deve estar no formato YYYY-MM-DD")
                
        if processo.data_entrega:
            try:
                datetime.strptime(processo.data_entrega, '%Y-%m-%d')
            except ValueError:
                erros.append("Data de entrega deve estar no formato YYYY-MM-DD")
                
        return erros