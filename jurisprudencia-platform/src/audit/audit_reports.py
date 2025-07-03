#!/usr/bin/env python3
"""
📊 GERADOR DE RELATÓRIOS DE AUDITORIA
Cria relatórios detalhados e dashboards de auditoria
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from jinja2 import Template
import logging
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from .audit_service import AuditService, AuditEventType, AuditSeverity

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditReportGenerator:
    """Gerador de relatórios de auditoria"""
    
    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configurar estilos customizados"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=30,
            alignment=1  # Center
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        ))
    
    async def generate_dashboard(self, start_date: datetime, end_date: datetime) -> str:
        """Gerar dashboard HTML interativo"""
        # Buscar dados
        logs = await self.audit_service.search_logs({
            'start_date': start_date,
            'end_date': end_date
        }, limit=10000)
        
        # Converter para DataFrame
        df = pd.DataFrame(logs)
        if df.empty:
            return self._empty_dashboard()
        
        # Preparar dados
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['date'] = df['timestamp'].dt.date
        
        # Criar visualizações
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Eventos por Tipo', 'Eventos por Severidade',
                'Timeline de Eventos', 'Top Usuários',
                'Eventos por Hora', 'Taxa de Erro'
            ),
            specs=[
                [{'type': 'pie'}, {'type': 'pie'}],
                [{'type': 'scatter', 'colspan': 2}, None],
                [{'type': 'bar'}, {'type': 'indicator'}]
            ]
        )
        
        # 1. Eventos por tipo
        event_counts = df['event_type'].value_counts()
        fig.add_trace(
            go.Pie(labels=event_counts.index, values=event_counts.values),
            row=1, col=1
        )
        
        # 2. Eventos por severidade
        severity_counts = df['severity'].value_counts()
        colors_map = {
            'critical': '#d32f2f',
            'error': '#f44336',
            'warning': '#ff9800',
            'info': '#2196f3',
            'debug': '#9e9e9e'
        }
        fig.add_trace(
            go.Pie(
                labels=severity_counts.index,
                values=severity_counts.values,
                marker=dict(colors=[colors_map.get(s, '#666') for s in severity_counts.index])
            ),
            row=1, col=2
        )
        
        # 3. Timeline de eventos
        timeline = df.groupby(['date', 'severity']).size().reset_index(name='count')
        for severity in timeline['severity'].unique():
            severity_data = timeline[timeline['severity'] == severity]
            fig.add_trace(
                go.Scatter(
                    x=severity_data['date'],
                    y=severity_data['count'],
                    mode='lines+markers',
                    name=severity,
                    line=dict(color=colors_map.get(severity, '#666'))
                ),
                row=2, col=1
            )
        
        # 4. Top usuários
        user_counts = df[df['user_name'].notna()]['user_name'].value_counts().head(10)
        fig.add_trace(
            go.Bar(x=user_counts.values, y=user_counts.index, orientation='h'),
            row=3, col=1
        )
        
        # 5. Taxa de erro
        error_rate = len(df[df['result'] == 'error']) / len(df) * 100
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=error_rate,
                title={'text': "Taxa de Erro (%)"},
                delta={'reference': 5, 'relative': True},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkred" if error_rate > 10 else "orange" if error_rate > 5 else "green"},
                    'steps': [
                        {'range': [0, 5], 'color': "lightgreen"},
                        {'range': [5, 10], 'color': "yellow"},
                        {'range': [10, 100], 'color': "lightcoral"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 10
                    }
                }
            ),
            row=3, col=2
        )
        
        # Atualizar layout
        fig.update_layout(
            title=f"Dashboard de Auditoria - {start_date.date()} a {end_date.date()}",
            showlegend=True,
            height=1200,
            template='plotly_white'
        )
        
        # Gerar HTML
        html_template = Template("""
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard de Auditoria</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e9ecef;
        }
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            color: #1a73e8;
            margin: 10px 0;
        }
        .stat-label {
            color: #666;
            font-size: 14px;
        }
        .recent-events {
            margin-top: 40px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: 600;
        }
        .severity-critical { color: #d32f2f; }
        .severity-error { color: #f44336; }
        .severity-warning { color: #ff9800; }
        .severity-info { color: #2196f3; }
        .severity-debug { color: #9e9e9e; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Dashboard de Auditoria</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total de Eventos</div>
                <div class="stat-value">{{ total_events }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Usuários Únicos</div>
                <div class="stat-value">{{ unique_users }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Taxa de Erro</div>
                <div class="stat-value">{{ error_rate }}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Tempo Médio</div>
                <div class="stat-value">{{ avg_duration }}ms</div>
            </div>
        </div>
        
        <div id="plotly-div"></div>
        
        <div class="recent-events">
            <h2>Eventos Recentes Críticos</h2>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Tipo</th>
                        <th>Severidade</th>
                        <th>Usuário</th>
                        <th>Ação</th>
                        <th>Resultado</th>
                    </tr>
                </thead>
                <tbody>
                    {% for event in recent_critical %}
                    <tr>
                        <td>{{ event.timestamp }}</td>
                        <td>{{ event.event_type }}</td>
                        <td class="severity-{{ event.severity }}">{{ event.severity }}</td>
                        <td>{{ event.user_name or '-' }}</td>
                        <td>{{ event.action or '-' }}</td>
                        <td>{{ event.result }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        var plotlyDiv = document.getElementById('plotly-div');
        var data = {{ plotly_json }};
        var layout = {{ layout_json }};
        Plotly.newPlot(plotlyDiv, data, layout);
    </script>
</body>
</html>
        """)
        
        # Calcular estatísticas
        stats = {
            'total_events': len(df),
            'unique_users': df['user_id'].nunique(),
            'error_rate': round(error_rate, 2),
            'avg_duration': round(df['duration_ms'].mean(), 2) if 'duration_ms' in df else 0,
            'recent_critical': df[df['severity'].isin(['critical', 'error'])].head(10).to_dict('records'),
            'plotly_json': fig.to_json(),
            'layout_json': json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder)
        }
        
        return html_template.render(**stats)
    
    def _empty_dashboard(self) -> str:
        """Dashboard vazio"""
        return """
        <html>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>Nenhum dado de auditoria encontrado</h1>
            <p>Não há eventos de auditoria no período selecionado.</p>
        </body>
        </html>
        """
    
    async def generate_compliance_report(self, start_date: datetime, 
                                       end_date: datetime) -> bytes:
        """Gerar relatório de compliance em PDF"""
        # Buscar dados
        logs = await self.audit_service.search_logs({
            'start_date': start_date,
            'end_date': end_date
        }, limit=50000)
        
        # Estatísticas
        stats = await self.audit_service.get_statistics(start_date, end_date)
        
        # Criar PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container para elementos
        elements = []
        
        # Título
        elements.append(Paragraph(
            "Relatório de Compliance - Auditoria",
            self.styles['CustomTitle']
        ))
        
        elements.append(Paragraph(
            f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}",
            self.styles['Normal']
        ))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Sumário executivo
        elements.append(Paragraph("Sumário Executivo", self.styles['SectionTitle']))
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Total de Eventos', f"{len(logs):,}"],
            ['Eventos Críticos', f"{len([l for l in logs if l['severity'] in ['critical', 'error']]):,}"],
            ['Taxa de Conformidade', f"{self._calculate_compliance_rate(logs):.1f}%"],
            ['Usuários Ativos', f"{len(set(l['user_id'] for l in logs if l.get('user_id'))):,}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Eventos por tipo
        elements.append(Paragraph("Distribuição de Eventos", self.styles['SectionTitle']))
        
        event_types = {}
        for log in logs:
            event_type = log['event_type']
            if event_type not in event_types:
                event_types[event_type] = 0
            event_types[event_type] += 1
        
        event_data = [['Tipo de Evento', 'Quantidade', 'Percentual']]
        total = len(logs)
        for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            event_data.append([event_type, f"{count:,}", f"{percentage:.1f}%"])
        
        event_table = Table(event_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        event_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(event_table)
        elements.append(PageBreak())
        
        # Análise de segurança
        elements.append(Paragraph("Análise de Segurança", self.styles['SectionTitle']))
        
        security_events = [
            l for l in logs 
            if l['event_type'] in ['login_failed', 'unauthorized_access', 'security_alert']
        ]
        
        if security_events:
            elements.append(Paragraph(
                f"Foram identificados {len(security_events)} eventos de segurança no período.",
                self.styles['Normal']
            ))
            
            # Top IPs suspeitos
            ip_counts = {}
            for event in security_events:
                ip = event.get('ip_address', 'Unknown')
                if ip not in ip_counts:
                    ip_counts[ip] = 0
                ip_counts[ip] += 1
            
            ip_data = [['IP Address', 'Eventos', 'Risco']]
            for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                risk = 'Alto' if count > 10 else 'Médio' if count > 5 else 'Baixo'
                ip_data.append([ip, str(count), risk])
            
            ip_table = Table(ip_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            ip_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(ip_table)
        else:
            elements.append(Paragraph(
                "Nenhum evento de segurança crítico foi identificado no período.",
                self.styles['Normal']
            ))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Recomendações
        elements.append(Paragraph("Recomendações", self.styles['SectionTitle']))
        
        recommendations = self._generate_recommendations(logs, stats)
        for i, rec in enumerate(recommendations, 1):
            elements.append(Paragraph(f"{i}. {rec}", self.styles['Normal']))
        
        # Gerar PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def _calculate_compliance_rate(self, logs: List[Dict]) -> float:
        """Calcular taxa de conformidade"""
        if not logs:
            return 100.0
        
        # Eventos que indicam não conformidade
        non_compliant_events = [
            'unauthorized_access',
            'security_alert',
            'permission_violation',
            'data_breach'
        ]
        
        non_compliant_count = len([
            l for l in logs 
            if l['event_type'] in non_compliant_events
        ])
        
        compliance_rate = ((len(logs) - non_compliant_count) / len(logs)) * 100
        return compliance_rate
    
    def _generate_recommendations(self, logs: List[Dict], stats: Dict) -> List[str]:
        """Gerar recomendações baseadas nos dados"""
        recommendations = []
        
        # Análise de falhas de login
        login_failures = len([l for l in logs if l['event_type'] == 'login_failed'])
        if login_failures > 100:
            recommendations.append(
                "Implementar políticas mais rígidas de bloqueio de conta após múltiplas tentativas falhas."
            )
        
        # Análise de horários
        night_events = len([
            l for l in logs 
            if pd.to_datetime(l['timestamp']).hour not in range(6, 22)
        ])
        if night_events > len(logs) * 0.3:
            recommendations.append(
                "Revisar acessos fora do horário comercial e implementar alertas para acessos suspeitos."
            )
        
        # Taxa de erro
        error_events = len([l for l in logs if l.get('result') == 'error'])
        if error_events > len(logs) * 0.05:
            recommendations.append(
                "Taxa de erro acima de 5%. Investigar causas e implementar melhorias na estabilidade."
            )
        
        # Sempre incluir
        recommendations.extend([
            "Manter logs de auditoria por pelo menos 1 ano para conformidade regulatória.",
            "Realizar revisões periódicas dos logs de auditoria para identificar padrões anômalos.",
            "Implementar alertas automáticos para eventos críticos de segurança."
        ])
        
        return recommendations
    
    async def generate_user_activity_report(self, user_id: str, 
                                          days: int = 30) -> Dict:
        """Gerar relatório de atividade de usuário específico"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Buscar logs do usuário
        logs = await self.audit_service.search_logs({
            'user_id': user_id,
            'start_date': start_date,
            'end_date': end_date
        }, limit=10000)
        
        if not logs:
            return {
                'user_id': user_id,
                'period_days': days,
                'total_events': 0,
                'message': 'Nenhuma atividade encontrada para este usuário.'
            }
        
        # Análise
        df = pd.DataFrame(logs)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Estatísticas
        report = {
            'user_id': user_id,
            'user_name': logs[0].get('user_name', 'Unknown'),
            'period_days': days,
            'total_events': len(logs),
            'first_activity': df['timestamp'].min().isoformat(),
            'last_activity': df['timestamp'].max().isoformat(),
            'event_types': df['event_type'].value_counts().to_dict(),
            'severity_distribution': df['severity'].value_counts().to_dict(),
            'unique_ips': df['ip_address'].nunique(),
            'ip_list': df['ip_address'].value_counts().head(5).to_dict(),
            'error_count': len(df[df['result'] == 'error']),
            'success_count': len(df[df['result'] == 'success']),
            'resources_accessed': df[df['resource_type'].notna()]['resource_type'].value_counts().to_dict(),
            'daily_activity': df.groupby(df['timestamp'].dt.date).size().to_dict(),
            'hourly_pattern': df.groupby(df['timestamp'].dt.hour).size().to_dict(),
            'suspicious_activities': self._identify_suspicious_activities(df)
        }
        
        return report
    
    def _identify_suspicious_activities(self, df: pd.DataFrame) -> List[Dict]:
        """Identificar atividades suspeitas"""
        suspicious = []
        
        # Múltiplas falhas de login
        login_failures = df[df['event_type'] == 'login_failed']
        if len(login_failures) > 5:
            suspicious.append({
                'type': 'multiple_login_failures',
                'count': len(login_failures),
                'severity': 'high'
            })
        
        # Acesso fora de horário
        night_access = df[(df['timestamp'].dt.hour < 6) | (df['timestamp'].dt.hour > 22)]
        if len(night_access) > 0:
            suspicious.append({
                'type': 'after_hours_access',
                'count': len(night_access),
                'severity': 'medium'
            })
        
        # Múltiplos IPs
        unique_ips = df['ip_address'].nunique()
        if unique_ips > 5:
            suspicious.append({
                'type': 'multiple_ip_addresses',
                'count': unique_ips,
                'severity': 'medium'
            })
        
        return suspicious


# Função auxiliar para gerar relatórios agendados
async def scheduled_report_generator(audit_service: AuditService,
                                   report_type: str = 'daily'):
    """Gerar relatórios agendados"""
    generator = AuditReportGenerator(audit_service)
    
    # Determinar período
    end_date = datetime.utcnow()
    if report_type == 'daily':
        start_date = end_date - timedelta(days=1)
    elif report_type == 'weekly':
        start_date = end_date - timedelta(days=7)
    elif report_type == 'monthly':
        start_date = end_date - timedelta(days=30)
    else:
        raise ValueError(f"Tipo de relatório inválido: {report_type}")
    
    # Gerar relatórios
    dashboard_html = await generator.generate_dashboard(start_date, end_date)
    compliance_pdf = await generator.generate_compliance_report(start_date, end_date)
    
    # Salvar arquivos
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    # Dashboard HTML
    dashboard_path = f"reports/audit_dashboard_{report_type}_{timestamp}.html"
    os.makedirs(os.path.dirname(dashboard_path), exist_ok=True)
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    
    # Compliance PDF
    compliance_path = f"reports/audit_compliance_{report_type}_{timestamp}.pdf"
    with open(compliance_path, 'wb') as f:
        f.write(compliance_pdf)
    
    logger.info(f"Relatórios {report_type} gerados: {dashboard_path}, {compliance_path}")
    
    return {
        'dashboard_path': dashboard_path,
        'compliance_path': compliance_path,
        'period': f"{start_date.date()} to {end_date.date()}"
    }