#!/usr/bin/env python3
"""Suite de testes para validar os módulos implementados."""

import sys
import os
import time
import argparse
import traceback
from typing import List, Dict, Any

# Adicionar diretório utils ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Importar módulos para teste
try:
    from tab_order_manager import TabOrderManager
    from ui_config import UIColors, UIButtonConfig, UIInputConfig, UILabelConfig, UITableConfig
    from advanced_cache import AdvancedCache, QueryCache, CacheDecorator
    from structured_logging import StructuredLogger, AsyncLogHandler
    from error_handling import ErrorHandler, ErrorType, ErrorSeverity
    from database_optimizer import QueryOptimizer, ConnectionPool
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    sys.exit(1)


class TestResult:
    """Resultado de um teste."""
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration


class TestSuite:
    """Suite principal de testes."""
    
    def __init__(self, quick_mode: bool = False):
        self.quick_mode = quick_mode
        self.results: List[TestResult] = []
        self.start_time = 0.0
    
    def run_test(self, test_func, test_name: str) -> TestResult:
        """Executa um teste individual."""
        print(f"Executando: {test_name}...", end=" ")
        
        start_time = time.time()
        try:
            test_func()
            duration = time.time() - start_time
            result = TestResult(test_name, True, "OK", duration)
            print(f"✅ OK ({duration:.3f}s)")
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            if not self.quick_mode:
                error_msg += f"\n{traceback.format_exc()}"
            result = TestResult(test_name, False, error_msg, duration)
            print(f"❌ FALHOU ({duration:.3f}s)")
            if not self.quick_mode:
                print(f"   Erro: {error_msg}")
        
        self.results.append(result)
        return result
    
    def test_tab_order_manager(self):
        """Testa TabOrderManager."""
        manager = TabOrderManager()
        
        # Teste básico de adição de widgets
        class MockWidget:
            def __init__(self, name):
                self.name = name
            def focus_set(self):
                pass
            def winfo_viewable(self):
                return True
            def winfo_exists(self):
                return True
            def cget(self, option):
                return 'normal'
        
        widget1 = MockWidget("widget1")
        widget2 = MockWidget("widget2")
        
        manager.add_widget(widget1, 1)
        manager.add_widget(widget2, 2)
        
        assert len(manager.widgets) == 2
        assert manager.widgets[0][1] == widget1
        assert manager.widgets[1][1] == widget2
    
    def test_ui_colors(self):
        """Testa UIColors."""
        # Verificar se as cores estão definidas
        assert hasattr(UIColors, 'PRIMARY')
        assert hasattr(UIColors, 'SECONDARY')
        assert hasattr(UIColors, 'SUCCESS')
        assert hasattr(UIColors, 'WARNING')
        assert hasattr(UIColors, 'DANGER')
        assert hasattr(UIColors, 'BACKGROUND_WHITE')
        assert hasattr(UIColors, 'TEXT_PRIMARY')
        
        # Verificar formato das cores (devem ser strings hexadecimais)
        assert UIColors.PRIMARY.startswith('#')
        assert len(UIColors.PRIMARY) == 7
    
    def test_ui_button_config(self):
        """Testa UIButtonConfig."""
        # Criar root temporário para inicializar fontes
        import tkinter as tk
        temp_root = tk.Tk()
        temp_root.withdraw()  # Ocultar janela
        
        try:
            # Testar métodos de configuração
            primary_config = UIButtonConfig.get_primary_config()
            assert isinstance(primary_config, dict)
            assert 'bg' in primary_config
            assert 'fg' in primary_config
            
            secondary_config = UIButtonConfig.get_secondary_config()
            assert isinstance(secondary_config, dict)
            
            success_config = UIButtonConfig.get_success_config()
            assert isinstance(success_config, dict)
        finally:
            temp_root.destroy()
    
    def test_advanced_cache(self):
        """Testa AdvancedCache."""
        cache = AdvancedCache(max_size=10)
        
        # Teste básico de put/get
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Teste de chave inexistente
        assert cache.get("key_inexistente") is None
        
        # Teste de TTL
        cache.put("key_ttl", "value_ttl", ttl=0.1)
        time.sleep(0.2)
        assert cache.get("key_ttl") is None
        
        # Teste de estatísticas
        stats = cache.get_stats()
        assert stats is not None
        assert hasattr(stats, 'hits')
        assert hasattr(stats, 'misses')
    
    def test_query_cache(self):
        """Testa QueryCache."""
        cache = QueryCache()
        
        # Teste básico
        sql = "SELECT * FROM users"
        params = ()
        result_data = []
        cache.put_query(sql, params, result_data, tags={"users"})
        result = cache.get_query(sql, params)
        assert result == []
        
        # Teste de invalidação por tag
        cache.invalidate_by_tags("users")
        result = cache.get_query(sql, params)
        assert result is None
    
    def test_cache_decorator(self):
        """Testa CacheDecorator."""
        cache = AdvancedCache()
        
        call_count = 0
        
        @CacheDecorator(cache, ttl=1.0)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # Primeira chamada
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Segunda chamada (deve usar cache)
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Não deve ter incrementado
    
    def test_structured_logging(self):
        """Testa StructuredLogger."""
        logger = StructuredLogger("test_logger")
        
        # Teste básico de log
        logger.info("Teste de log", extra_data={"key": "value"})
        logger.warning("Teste de warning")
        logger.error("Teste de error")
        
        # Verificar se o logger foi criado
        assert logger.logger is not None
        assert logger.logger.name == "test_logger"
    
    def test_async_log_handler(self):
        """Testa AsyncLogHandler."""
        import logging
        base_handler = logging.StreamHandler()
        handler = AsyncLogHandler(base_handler)
        
        # Verificar se o handler foi inicializado
        assert handler.queue is not None
        assert handler._stop_event is not None
        
        # Parar o handler
        handler.close()
    
    def test_error_handling(self):
        """Testa ErrorHandler."""
        handler = ErrorHandler()
        
        # Teste de registro de erro
        try:
            raise ValueError("Erro de teste")
        except Exception as e:
            error_id = handler.handle_error(
                e, 
                ErrorType.VALIDATION, 
                ErrorSeverity.MEDIUM,
                context={"test": True}
            )
            assert error_id is not None
        
        # Verificar estatísticas
        stats = handler.get_error_stats()
        assert isinstance(stats, dict)
        assert 'total_errors' in stats
    
    def test_database_optimizer(self):
        """Testa QueryOptimizer (sem banco real)."""
        # Teste básico de inicialização
        optimizer = QueryOptimizer(":memory:")
        
        # Verificar se foi inicializado
        assert optimizer.database_path == ":memory:"
        assert optimizer.connection_pool is not None
        assert isinstance(optimizer.query_stats, dict)
        
        # Teste de normalização de query
        normalized = optimizer._normalize_query("SELECT * FROM users WHERE id = 123")
        assert "?" in normalized
        assert "123" not in normalized
        
        # Fechar optimizer
        optimizer.close()
    
    def test_connection_pool(self):
        """Testa ConnectionPool."""
        pool = ConnectionPool(":memory:", max_connections=2)
        
        # Obter conexão
        conn = pool.get_connection()
        assert conn is not None
        
        # Retornar conexão
        pool.return_connection(conn)
        
        # Fechar pool
        pool.close_all()
    
    def run_all_tests(self):
        """Executa todos os testes."""
        print("🚀 Iniciando suite de testes...")
        print(f"Modo: {'Rápido' if self.quick_mode else 'Completo'}")
        print("-" * 50)
        
        self.start_time = time.time()
        
        # Lista de testes
        tests = [
            (self.test_tab_order_manager, "TabOrderManager"),
            (self.test_ui_colors, "UIColors"),
            (self.test_ui_button_config, "UIButtonConfig"),
            (self.test_advanced_cache, "AdvancedCache"),
            (self.test_query_cache, "QueryCache"),
            (self.test_cache_decorator, "CacheDecorator"),
            (self.test_structured_logging, "StructuredLogger"),
            (self.test_async_log_handler, "AsyncLogHandler"),
            (self.test_error_handling, "ErrorHandler"),
            (self.test_database_optimizer, "QueryOptimizer"),
            (self.test_connection_pool, "ConnectionPool"),
        ]
        
        # Executar testes
        for test_func, test_name in tests:
            self.run_test(test_func, test_name)
        
        # Relatório final
        self.print_summary()
    
    def print_summary(self):
        """Imprime resumo dos testes."""
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        print("-" * 50)
        print(f"📊 RESUMO DOS TESTES")
        print(f"Total: {len(self.results)}")
        print(f"✅ Passou: {passed}")
        print(f"❌ Falhou: {failed}")
        print(f"⏱️  Tempo total: {total_time:.3f}s")
        
        if failed > 0:
            print("\n❌ TESTES FALHARAM:")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.name}: {result.message}")
        
        success_rate = (passed / len(self.results)) * 100
        print(f"\n🎯 Taxa de sucesso: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 Todos os testes passaram!")
        elif success_rate >= 80:
            print("⚠️  Maioria dos testes passou, mas há falhas.")
        else:
            print("🚨 Muitos testes falharam, revisão necessária.")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description="Suite de testes dos módulos")
    parser.add_argument(
        "--quick", 
        action="store_true", 
        help="Modo rápido (sem stack traces detalhados)"
    )
    
    args = parser.parse_args()
    
    # Executar testes
    suite = TestSuite(quick_mode=args.quick)
    suite.run_all_tests()
    
    # Código de saída baseado nos resultados
    failed_count = sum(1 for r in suite.results if not r.passed)
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()