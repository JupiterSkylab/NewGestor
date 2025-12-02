"""Sistema de monitoramento de cache para MiniGestor TRAE.

Este módulo fornece ferramentas para monitorar o desempenho do cache,
identificar gargalos e otimizar o uso de memória.
"""

import time
import threading
import psutil
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from .intelligent_cache import get_intelligent_cache


@dataclass
class CacheMetrics:
    """Métricas de performance do cache."""
    timestamp: datetime
    hit_rate: float
    memory_usage_mb: float
    entry_count: int
    hits: int
    misses: int
    evictions: int
    system_memory_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class CacheAlert:
    """Alerta de cache."""
    timestamp: datetime
    level: str  # INFO, WARNING, ERROR
    message: str
    metric_name: str
    current_value: float
    threshold: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class CacheMonitor:
    """Monitor de performance do cache."""
    
    def __init__(self, 
                 check_interval: float = 30.0,
                 history_size: int = 1000,
                 memory_threshold: float = 80.0,
                 hit_rate_threshold: float = 0.7):
        
        self.check_interval = check_interval
        self.history_size = history_size
        self.memory_threshold = memory_threshold
        self.hit_rate_threshold = hit_rate_threshold
        
        self.logger = logging.getLogger(__name__)
        self.cache = get_intelligent_cache()
        
        # Histórico de métricas
        self.metrics_history: List[CacheMetrics] = []
        self.alerts_history: List[CacheAlert] = []
        
        # Controle de thread
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Callbacks para alertas
        self._alert_callbacks: List[callable] = []
    
    def start_monitoring(self):
        """Inicia o monitoramento em background."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="CacheMonitor"
        )
        self._monitor_thread.start()
        self.logger.info("Monitoramento de cache iniciado")
    
    def stop_monitoring(self):
        """Para o monitoramento."""
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        self.logger.info("Monitoramento de cache parado")
    
    def _monitor_loop(self):
        """Loop principal de monitoramento."""
        while self._monitoring:
            try:
                self._collect_metrics()
                self._check_alerts()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Erro no monitoramento de cache: {e}")
                time.sleep(self.check_interval)
    
    def _collect_metrics(self):
        """Coleta métricas atuais do cache."""
        try:
            # Estatísticas do cache
            cache_stats = self.cache.get_cache_stats()
            memory_usage = self.cache.get_memory_usage()
            
            # Estatísticas do sistema
            system_memory = psutil.virtual_memory()
            
            # Criar métrica
            metrics = CacheMetrics(
                timestamp=datetime.now(),
                hit_rate=cache_stats['app_cache']['hit_rate'],
                memory_usage_mb=memory_usage['total_mb'],
                entry_count=cache_stats['app_cache']['entry_count'],
                hits=cache_stats['app_cache']['hits'],
                misses=cache_stats['app_cache']['misses'],
                evictions=0,  # TODO: Implementar contagem de evictions
                system_memory_percent=system_memory.percent
            )
            
            # Adicionar ao histórico
            with self._lock:
                self.metrics_history.append(metrics)
                
                # Manter tamanho do histórico
                if len(self.metrics_history) > self.history_size:
                    self.metrics_history.pop(0)
            
            self.logger.debug(f"Métricas coletadas: hit_rate={metrics.hit_rate:.2%}, "
                            f"memory={metrics.memory_usage_mb:.1f}MB")
            
        except Exception as e:
            self.logger.error(f"Erro ao coletar métricas: {e}")
    
    def _check_alerts(self):
        """Verifica condições de alerta."""
        if not self.metrics_history:
            return
        
        current_metrics = self.metrics_history[-1]
        
        # Verificar uso de memória
        if current_metrics.memory_usage_mb > self.memory_threshold:
            self._create_alert(
                "WARNING",
                f"Uso de memória do cache alto: {current_metrics.memory_usage_mb:.1f}MB",
                "memory_usage",
                current_metrics.memory_usage_mb,
                self.memory_threshold
            )
        
        # Verificar taxa de acerto
        if (current_metrics.hits + current_metrics.misses > 100 and 
            current_metrics.hit_rate < self.hit_rate_threshold):
            self._create_alert(
                "WARNING",
                f"Taxa de acerto baixa: {current_metrics.hit_rate:.2%}",
                "hit_rate",
                current_metrics.hit_rate,
                self.hit_rate_threshold
            )
        
        # Verificar memória do sistema
        if current_metrics.system_memory_percent > 90:
            self._create_alert(
                "ERROR",
                f"Memória do sistema crítica: {current_metrics.system_memory_percent:.1f}%",
                "system_memory",
                current_metrics.system_memory_percent,
                90.0
            )
    
    def _create_alert(self, level: str, message: str, metric_name: str, 
                     current_value: float, threshold: float):
        """Cria um alerta."""
        alert = CacheAlert(
            timestamp=datetime.now(),
            level=level,
            message=message,
            metric_name=metric_name,
            current_value=current_value,
            threshold=threshold
        )
        
        with self._lock:
            self.alerts_history.append(alert)
            
            # Manter tamanho do histórico
            if len(self.alerts_history) > self.history_size:
                self.alerts_history.pop(0)
        
        # Log do alerta
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"Cache Alert [{level}]: {message}")
        
        # Executar callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Erro em callback de alerta: {e}")
    
    def add_alert_callback(self, callback: callable):
        """Adiciona callback para alertas."""
        self._alert_callbacks.append(callback)
    
    def get_current_metrics(self) -> Optional[CacheMetrics]:
        """Retorna métricas atuais."""
        with self._lock:
            return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, hours: int = 24) -> List[CacheMetrics]:
        """Retorna histórico de métricas."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            return [
                m for m in self.metrics_history 
                if m.timestamp >= cutoff_time
            ]
    
    def get_alerts_history(self, hours: int = 24) -> List[CacheAlert]:
        """Retorna histórico de alertas."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            return [
                a for a in self.alerts_history 
                if a.timestamp >= cutoff_time
            ]
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Retorna resumo de performance."""
        metrics = self.get_metrics_history(hours)
        alerts = self.get_alerts_history(hours)
        
        if not metrics:
            return {"error": "Nenhuma métrica disponível"}
        
        # Calcular estatísticas
        hit_rates = [m.hit_rate for m in metrics if m.hits + m.misses > 0]
        memory_usage = [m.memory_usage_mb for m in metrics]
        
        return {
            "period_hours": hours,
            "total_samples": len(metrics),
            "hit_rate": {
                "current": metrics[-1].hit_rate if metrics else 0,
                "average": sum(hit_rates) / len(hit_rates) if hit_rates else 0,
                "min": min(hit_rates) if hit_rates else 0,
                "max": max(hit_rates) if hit_rates else 0
            },
            "memory_usage_mb": {
                "current": metrics[-1].memory_usage_mb if metrics else 0,
                "average": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                "min": min(memory_usage) if memory_usage else 0,
                "max": max(memory_usage) if memory_usage else 0
            },
            "alerts": {
                "total": len(alerts),
                "by_level": {
                    level: len([a for a in alerts if a.level == level])
                    for level in ["INFO", "WARNING", "ERROR"]
                }
            },
            "cache_entries": metrics[-1].entry_count if metrics else 0,
            "total_hits": metrics[-1].hits if metrics else 0,
            "total_misses": metrics[-1].misses if metrics else 0
        }
    
    def optimize_cache(self) -> Dict[str, Any]:
        """Executa otimizações automáticas do cache."""
        results = {
            "actions_taken": [],
            "recommendations": []
        }
        
        current_metrics = self.get_current_metrics()
        if not current_metrics:
            return results
        
        # Limpeza se uso de memória alto
        if current_metrics.memory_usage_mb > self.memory_threshold:
            # Limpar cache de estatísticas (menos crítico)
            self.cache.invalidate_statistics()
            results["actions_taken"].append("Limpeza de cache de estatísticas")
        
        # Recomendações baseadas na performance
        if current_metrics.hit_rate < 0.5:
            results["recommendations"].append(
                "Taxa de acerto baixa - considere aumentar TTL dos caches"
            )
        
        if current_metrics.memory_usage_mb > 50:
            results["recommendations"].append(
                "Alto uso de memória - considere reduzir tamanho máximo do cache"
            )
        
        return results
    
    def export_metrics(self, format: str = "json") -> str:
        """Exporta métricas em formato especificado."""
        metrics = self.get_metrics_history()
        alerts = self.get_alerts_history()
        
        data = {
            "export_timestamp": datetime.now().isoformat(),
            "metrics": [m.to_dict() for m in metrics],
            "alerts": [a.to_dict() for a in alerts],
            "summary": self.get_performance_summary()
        }
        
        if format.lower() == "json":
            import json
            return json.dumps(data, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Formato não suportado: {format}")
    
    def __del__(self):
        """Destrutor para garantir limpeza."""
        try:
            self.stop_monitoring()
        except:
            pass


# Instância global do monitor
_global_cache_monitor: Optional[CacheMonitor] = None


def get_cache_monitor() -> CacheMonitor:
    """Retorna instância global do monitor de cache."""
    global _global_cache_monitor
    if _global_cache_monitor is None:
        _global_cache_monitor = CacheMonitor()
    return _global_cache_monitor


def start_cache_monitoring():
    """Inicia monitoramento global do cache."""
    monitor = get_cache_monitor()
    monitor.start_monitoring()


def stop_cache_monitoring():
    """Para monitoramento global do cache."""
    global _global_cache_monitor
    if _global_cache_monitor is not None:
        _global_cache_monitor.stop_monitoring()
        _global_cache_monitor = None


if __name__ == "__main__":
    # Exemplo de uso
    logging.basicConfig(level=logging.INFO)
    
    monitor = CacheMonitor(check_interval=5.0)
    
    # Callback de exemplo para alertas
    def on_alert(alert: CacheAlert):
        print(f"ALERTA [{alert.level}]: {alert.message}")
    
    monitor.add_alert_callback(on_alert)
    monitor.start_monitoring()
    
    try:
        # Simular uso por 30 segundos
        time.sleep(30)
        
        # Mostrar resumo
        summary = monitor.get_performance_summary()
        print("\nResumo de Performance:")
        print(f"Taxa de acerto: {summary['hit_rate']['current']:.2%}")
        print(f"Uso de memória: {summary['memory_usage_mb']['current']:.1f}MB")
        print(f"Total de alertas: {summary['alerts']['total']}")
        
    finally:
        monitor.stop_monitoring()