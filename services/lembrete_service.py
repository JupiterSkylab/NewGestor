from typing import List, Optional, Tuple
from datetime import datetime
from database.repositories import LembreteRepository
import logging
from utils.intelligent_cache import get_intelligent_cache
from utils.structured_logger import get_logger, get_performance_logger, logged_method

class LembreteService:
    """Service layer para operações com lembretes/promessas."""
    
    def __init__(self, lembrete_repo: LembreteRepository):
        self.lembrete_repo = lembrete_repo
        self.logger = get_logger("lembrete_service")
        self.perf_logger = get_performance_logger("lembrete_service")
        self._intelligent_cache = get_intelligent_cache()
        
    @logged_method("criar_lembrete", log_args=True, log_performance=True)
    def criar_lembrete(self, data_prometida: str, descricao: str) -> Tuple[bool, str]:
        """Cria um novo lembrete com validações.
        
        Args:
            data_prometida: Data da promessa no formato dd/mm/aaaa.
            descricao: Descrição do lembrete.
            
        Returns:
            Tupla (sucesso, mensagem).
        """
        try:
            # Validações básicas
            if not data_prometida or not data_prometida.strip():
                return False, "Data prometida é obrigatória"
                
            if not descricao or not descricao.strip():
                return False, "Descrição é obrigatória"
                
            # Validação do formato da data
            if not self._validar_formato_data(data_prometida):
                return False, "Data deve estar no formato dd/mm/aaaa"
                
            success = self.lembrete_repo.create_lembrete(data_prometida.strip(), descricao.strip())
            if success:
                # Invalidar caches relacionados
                self._intelligent_cache.invalidate_reminders()
                
                self.logger.info(
                    f"Lembrete criado com sucesso: {data_prometida} - {descricao}",
                    extra_data={
                        'data_prometida': data_prometida.strip(),
                        'descricao': descricao.strip()
                    }
                )
                return True, "Lembrete criado com sucesso!"
            else:
                self.logger.error(
                    "Falha ao criar lembrete no repositório",
                    extra_data={
                        'data_prometida': data_prometida.strip(),
                        'descricao': descricao.strip()
                    }
                )
                return False, "Erro ao criar lembrete"
                
        except Exception as e:
            self.logger.error(
                f"Erro interno ao criar lembrete: {str(e)}",
                extra_data={
                    'data_prometida': data_prometida,
                    'descricao': descricao
                }
            )
            return False, f"Erro ao criar lembrete: {str(e)}"
            
    def atualizar_lembrete(self, rowid: int, data_prometida: str, descricao: str) -> Tuple[bool, str]:
        """Atualiza um lembrete existente.
        
        Args:
            rowid: ID do lembrete.
            data_prometida: Nova data da promessa.
            descricao: Nova descrição.
            
        Returns:
            Tupla (sucesso, mensagem).
        """
        try:
            # Validações básicas
            if not data_prometida or not data_prometida.strip():
                return False, "Data prometida é obrigatória"
                
            if not descricao or not descricao.strip():
                return False, "Descrição é obrigatória"
                
            # Validação do formato da data
            if not self._validar_formato_data(data_prometida):
                return False, "Data deve estar no formato dd/mm/aaaa"
                
            success = self.lembrete_repo.update_lembrete(rowid, data_prometida.strip(), descricao.strip())
            if success:
                # Invalidar caches relacionados
                self._intelligent_cache.invalidate_reminders()
                
                self.logger.info(f"Lembrete {rowid} atualizado com sucesso")
                return True, "Lembrete atualizado com sucesso!"
            else:
                return False, "Lembrete não encontrado"
                
        except Exception as e:
            self.logger.error(f"Erro ao atualizar lembrete: {e}")
            return False, f"Erro ao atualizar lembrete: {str(e)}"
            
    def excluir_lembrete(self, rowid: int) -> Tuple[bool, str]:
        """Exclui um lembrete.
        
        Args:
            rowid: ID do lembrete a ser excluído.
            
        Returns:
            Tupla (sucesso, mensagem).
        """
        try:
            success = self.lembrete_repo.delete_lembrete(rowid)
            if success:
                # Invalidar caches relacionados
                self._intelligent_cache.invalidate_reminders()
                
                self.logger.info(f"Lembrete {rowid} excluído com sucesso")
                return True, "Lembrete excluído com sucesso!"
            else:
                return False, "Lembrete não encontrado"
                
        except Exception as e:
            self.logger.error(f"Erro ao excluir lembrete: {e}")
            return False, f"Erro ao excluir lembrete: {str(e)}"
            
    def listar_lembretes(self) -> List[Tuple]:
        """Lista todos os lembretes.
        
        Returns:
            Lista de tuplas (rowid, data_prometida, descricao).
        """
        try:
            return self.lembrete_repo.get_all_lembretes()
        except Exception as e:
            self.logger.error(f"Erro ao listar lembretes: {e}")
            return []
            
    def obter_lembrete(self, rowid: int) -> Optional[Tuple]:
        """Obtém um lembrete pelo ID.
        
        Args:
            rowid: ID do lembrete.
            
        Returns:
            Tupla (rowid, data_prometida, descricao) ou None se não encontrado.
        """
        try:
            return self.lembrete_repo.get_lembrete_by_id(rowid)
        except Exception as e:
            self.logger.error(f"Erro ao obter lembrete: {e}")
            return None
            
    def buscar_lembretes(self, termo_busca: str) -> List[Tuple]:
        """Busca lembretes por termo.
        
        Args:
            termo_busca: Termo para buscar na descrição ou data.
            
        Returns:
            Lista de tuplas (rowid, data_prometida, descricao) encontradas.
        """
        try:
            if not termo_busca or not termo_busca.strip():
                return self.listar_lembretes()
                
            return self.lembrete_repo.search_lembretes(termo_busca.strip())
        except Exception as e:
            self.logger.error(f"Erro ao buscar lembretes: {e}")
            return []
            
    def contar_lembretes(self) -> int:
        """Conta o total de lembretes.
        
        Returns:
            Número total de lembretes.
        """
        try:
            return self.lembrete_repo.count_lembretes()
        except Exception as e:
            self.logger.error(f"Erro ao contar lembretes: {e}")
            return 0
            
    def verificar_lembretes_vencidos(self) -> List[Tuple]:
        """Verifica lembretes com data vencida.
        
        Returns:
            Lista de lembretes vencidos.
        """
        try:
            lembretes = self.lembrete_repo.get_all_lembretes()
            lembretes_vencidos = []
            data_hoje = datetime.now().date()
            
            for rowid, data_prometida, descricao in lembretes:
                try:
                    # Converte data dd/mm/aaaa para objeto date
                    data_obj = datetime.strptime(data_prometida, '%d/%m/%Y').date()
                    if data_obj < data_hoje:
                        lembretes_vencidos.append((rowid, data_prometida, descricao))
                except ValueError:
                    # Se não conseguir converter a data, considera como vencido para revisão
                    lembretes_vencidos.append((rowid, data_prometida, descricao))
                    
            return lembretes_vencidos
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar lembretes vencidos: {e}")
            return []
            
    def verificar_lembretes_proximos(self, dias: int = 7) -> List[Tuple]:
        """Verifica lembretes próximos ao vencimento.
        
        Args:
            dias: Número de dias para considerar como "próximo".
            
        Returns:
            Lista de lembretes próximos ao vencimento.
        """
        try:
            lembretes = self.lembrete_repo.get_all_lembretes()
            lembretes_proximos = []
            data_hoje = datetime.now().date()
            data_limite = data_hoje.replace(day=data_hoje.day + dias)
            
            for rowid, data_prometida, descricao in lembretes:
                try:
                    # Converte data dd/mm/aaaa para objeto date
                    data_obj = datetime.strptime(data_prometida, '%d/%m/%Y').date()
                    if data_hoje <= data_obj <= data_limite:
                        lembretes_proximos.append((rowid, data_prometida, descricao))
                except ValueError:
                    # Ignora datas inválidas
                    continue
                    
            return lembretes_proximos
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar lembretes próximos: {e}")
            return []
            
    def _validar_formato_data(self, data: str) -> bool:
        """Valida se a data está no formato dd/mm/aaaa.
        
        Args:
            data: String da data a ser validada.
            
        Returns:
            True se válida, False caso contrário.
        """
        try:
            datetime.strptime(data, '%d/%m/%Y')
            return True
        except ValueError:
            return False
            
    def formatar_data_para_exibicao(self, data: str) -> str:
        """Formata data para exibição consistente.
        
        Args:
            data: Data no formato dd/mm/aaaa.
            
        Returns:
            Data formatada ou string original se inválida.
        """
        try:
            data_obj = datetime.strptime(data, '%d/%m/%Y')
            return data_obj.strftime('%d/%m/%Y')
        except ValueError:
            return data  # Retorna original se não conseguir formatar