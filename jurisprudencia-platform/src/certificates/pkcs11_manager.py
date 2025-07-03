"""
🔏 GERENCIADOR DE CERTIFICADOS A3/TOKEN
Integração real com certificados digitais via PKCS#11
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime
import PyKCS11
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64
import json

logger = logging.getLogger(__name__)


class PKCS11Manager:
    """
    Gerenciador de certificados digitais A3/Token
    Suporta certificados em tokens USB e smartcards
    """
    
    # Bibliotecas PKCS#11 comuns
    PKCS11_LIBS = {
        'safenet': {
            'windows': 'eTPKCS11.dll',
            'linux': '/usr/lib/libeTPkcs11.so',
            'darwin': '/usr/local/lib/libeTPkcs11.dylib'
        },
        'gemalto': {
            'windows': 'gclib.dll',
            'linux': '/usr/lib/libgclib.so',
            'darwin': '/usr/local/lib/libgclib.dylib'
        },
        'watchdata': {
            'windows': 'WDPKCS.dll',
            'linux': '/usr/lib/libwdpkcs.so',
            'darwin': '/usr/local/lib/libwdpkcs.dylib'
        },
        'aladdin': {
            'windows': 'etpkcs11.dll',
            'linux': '/usr/lib/libeToken.so',
            'darwin': '/usr/local/lib/libeToken.dylib'
        }
    }
    
    def __init__(self, lib_path: Optional[str] = None):
        """
        Inicializa gerenciador PKCS#11
        
        Args:
            lib_path: Caminho para biblioteca PKCS#11 (auto-detecta se None)
        """
        self.pkcs11 = PyKCS11.PyKCS11Lib()
        self.lib_path = lib_path or self._auto_detect_lib()
        self.session = None
        self.logged_in = False
        
        if self.lib_path:
            self._load_library()
    
    def _auto_detect_lib(self) -> Optional[str]:
        """Auto-detecta biblioteca PKCS#11 instalada"""
        platform = sys.platform
        
        for provider, paths in self.PKCS11_LIBS.items():
            if platform.startswith('win'):
                lib_path = paths.get('windows')
            elif platform.startswith('linux'):
                lib_path = paths.get('linux')
            elif platform.startswith('darwin'):
                lib_path = paths.get('darwin')
            else:
                continue
            
            if lib_path and Path(lib_path).exists():
                logger.info(f"Biblioteca PKCS#11 detectada: {provider} - {lib_path}")
                return lib_path
        
        logger.warning("Nenhuma biblioteca PKCS#11 encontrada")
        return None
    
    def _load_library(self):
        """Carrega biblioteca PKCS#11"""
        try:
            self.pkcs11.load(self.lib_path)
            logger.info(f"Biblioteca PKCS#11 carregada: {self.lib_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar biblioteca PKCS#11: {e}")
            raise
    
    def list_available_slots(self) -> List[Dict]:
        """Lista slots disponíveis (tokens/smartcards)"""
        try:
            slots = self.pkcs11.getSlotList(tokenPresent=True)
            
            slot_info = []
            for slot in slots:
                info = self.pkcs11.getSlotInfo(slot)
                token_info = self.pkcs11.getTokenInfo(slot)
                
                slot_info.append({
                    'slot_id': slot,
                    'description': info.slotDescription.strip(),
                    'manufacturer': info.manufacturerID.strip(),
                    'hardware_version': f"{info.hardwareVersion.major}.{info.hardwareVersion.minor}",
                    'firmware_version': f"{info.firmwareVersion.major}.{info.firmwareVersion.minor}",
                    'token_label': token_info.label.strip(),
                    'token_manufacturer': token_info.manufacturerID.strip(),
                    'token_model': token_info.model.strip(),
                    'serial_number': token_info.serialNumber.strip()
                })
            
            return slot_info
            
        except Exception as e:
            logger.error(f"Erro ao listar slots: {e}")
            return []
    
    def open_session(self, slot_id: int) -> bool:
        """Abre sessão com o token"""
        try:
            self.session = self.pkcs11.openSession(slot_id, PyKCS11.CKF_SERIAL_SESSION | PyKCS11.CKF_RW_SESSION)
            logger.info(f"Sessão aberta no slot {slot_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao abrir sessão: {e}")
            return False
    
    def login(self, pin: str) -> bool:
        """Faz login no token com PIN"""
        if not self.session:
            logger.error("Nenhuma sessão aberta")
            return False
        
        try:
            self.session.login(pin)
            self.logged_in = True
            logger.info("Login realizado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False
    
    def logout(self):
        """Faz logout do token"""
        if self.session and self.logged_in:
            try:
                self.session.logout()
                self.logged_in = False
                logger.info("Logout realizado")
            except:
                pass
    
    def close_session(self):
        """Fecha sessão com o token"""
        if self.session:
            try:
                self.logout()
                self.session.closeSession()
                self.session = None
                logger.info("Sessão fechada")
            except:
                pass
    
    def list_certificates(self) -> List[Dict]:
        """Lista certificados disponíveis no token"""
        if not self.session or not self.logged_in:
            logger.error("Sessão não aberta ou não autenticada")
            return []
        
        try:
            # Buscar objetos de certificado
            template = [
                (PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE),
                (PyKCS11.CKA_CERTIFICATE_TYPE, PyKCS11.CKC_X_509)
            ]
            
            objects = self.session.findObjects(template)
            
            certificates = []
            for obj in objects:
                try:
                    # Obter atributos do certificado
                    attrs = self.session.getAttributeValue(obj, [
                        PyKCS11.CKA_LABEL,
                        PyKCS11.CKA_ID,
                        PyKCS11.CKA_VALUE,
                        PyKCS11.CKA_SUBJECT
                    ])
                    
                    label = attrs[0].decode('utf-8', errors='ignore') if attrs[0] else 'Sem label'
                    cert_id = bytes(attrs[1]).hex() if attrs[1] else ''
                    cert_der = bytes(attrs[2]) if attrs[2] else b''
                    
                    # Parse certificado X.509
                    if cert_der:
                        cert = x509.load_der_x509_certificate(cert_der, default_backend())
                        
                        # Extrair informações
                        subject_info = self._parse_x509_name(cert.subject)
                        issuer_info = self._parse_x509_name(cert.issuer)
                        
                        certificates.append({
                            'label': label,
                            'id': cert_id,
                            'subject': subject_info,
                            'issuer': issuer_info,
                            'serial_number': str(cert.serial_number),
                            'not_before': cert.not_valid_before.isoformat(),
                            'not_after': cert.not_valid_after.isoformat(),
                            'is_valid': self._is_cert_valid(cert),
                            'key_usage': self._get_key_usage(cert),
                            'certificate_object': obj
                        })
                    
                except Exception as e:
                    logger.error(f"Erro ao processar certificado: {e}")
            
            return certificates
            
        except Exception as e:
            logger.error(f"Erro ao listar certificados: {e}")
            return []
    
    def get_certificate_and_key(self, cert_id: str) -> Optional[Tuple[x509.Certificate, Any]]:
        """Obtém certificado e chave privada correspondente"""
        if not self.session or not self.logged_in:
            return None
        
        try:
            # Buscar certificado
            cert_template = [
                (PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE),
                (PyKCS11.CKA_ID, bytes.fromhex(cert_id))
            ]
            
            cert_objects = self.session.findObjects(cert_template)
            if not cert_objects:
                logger.error("Certificado não encontrado")
                return None
            
            # Obter certificado
            cert_attrs = self.session.getAttributeValue(cert_objects[0], [PyKCS11.CKA_VALUE])
            cert_der = bytes(cert_attrs[0])
            certificate = x509.load_der_x509_certificate(cert_der, default_backend())
            
            # Buscar chave privada correspondente
            key_template = [
                (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
                (PyKCS11.CKA_ID, bytes.fromhex(cert_id))
            ]
            
            key_objects = self.session.findObjects(key_template)
            if not key_objects:
                logger.error("Chave privada não encontrada")
                return None
            
            return (certificate, key_objects[0])
            
        except Exception as e:
            logger.error(f"Erro ao obter certificado e chave: {e}")
            return None
    
    def sign_data(self, data: bytes, cert_id: str, 
                  mechanism: int = PyKCS11.CKM_SHA256_RSA_PKCS) -> Optional[bytes]:
        """
        Assina dados usando certificado do token
        
        Args:
            data: Dados a assinar
            cert_id: ID do certificado
            mechanism: Mecanismo de assinatura
            
        Returns:
            Assinatura ou None se erro
        """
        if not self.session or not self.logged_in:
            logger.error("Sessão não autenticada")
            return None
        
        try:
            # Buscar chave privada
            key_template = [
                (PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
                (PyKCS11.CKA_ID, bytes.fromhex(cert_id))
            ]
            
            key_objects = self.session.findObjects(key_template)
            if not key_objects:
                logger.error("Chave privada não encontrada")
                return None
            
            # Assinar dados
            signature = self.session.sign(key_objects[0], data, mechanism)
            
            return bytes(signature)
            
        except Exception as e:
            logger.error(f"Erro ao assinar dados: {e}")
            return None
    
    def create_authenticated_session(self, cert_id: str, 
                                   target_url: str) -> Optional[Dict]:
        """
        Cria sessão autenticada com certificado para tribunal
        
        Args:
            cert_id: ID do certificado
            target_url: URL do tribunal
            
        Returns:
            Dados da sessão ou None
        """
        cert_and_key = self.get_certificate_and_key(cert_id)
        if not cert_and_key:
            return None
        
        certificate, key_handle = cert_and_key
        
        try:
            # Exportar certificado para PEM
            cert_pem = certificate.public_bytes(
                encoding=serialization.Encoding.PEM
            ).decode('utf-8')
            
            # Criar wrapper para chave privada no token
            # Nota: A chave privada permanece no token, não é exportada
            
            session_data = {
                'certificate_pem': cert_pem,
                'certificate_id': cert_id,
                'key_handle': key_handle,
                'target_url': target_url,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Em produção, isso seria integrado com requests/aiohttp
            # para criar uma sessão HTTPS com autenticação mútua
            
            return session_data
            
        except Exception as e:
            logger.error(f"Erro ao criar sessão autenticada: {e}")
            return None
    
    def _parse_x509_name(self, name: x509.Name) -> Dict[str, str]:
        """Parse nome X.509 para dicionário"""
        result = {}
        
        for attribute in name:
            oid = attribute.oid
            value = attribute.value
            
            # Mapear OIDs comuns
            oid_map = {
                x509.NameOID.COMMON_NAME: 'CN',
                x509.NameOID.ORGANIZATION_NAME: 'O',
                x509.NameOID.ORGANIZATIONAL_UNIT_NAME: 'OU',
                x509.NameOID.COUNTRY_NAME: 'C',
                x509.NameOID.STATE_OR_PROVINCE_NAME: 'ST',
                x509.NameOID.LOCALITY_NAME: 'L',
                x509.NameOID.EMAIL_ADDRESS: 'E'
            }
            
            key = oid_map.get(oid, oid.dotted_string)
            result[key] = value
        
        # Adicionar CPF/CNPJ se presente
        if 'CN' in result:
            cn = result['CN']
            if ':' in cn:
                parts = cn.split(':')
                if len(parts) >= 2:
                    result['NOME'] = parts[0]
                    result['CPF'] = parts[1]
        
        return result
    
    def _is_cert_valid(self, cert: x509.Certificate) -> bool:
        """Verifica se certificado está válido"""
        now = datetime.utcnow()
        return cert.not_valid_before <= now <= cert.not_valid_after
    
    def _get_key_usage(self, cert: x509.Certificate) -> List[str]:
        """Obtém usos permitidos do certificado"""
        try:
            ext = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.KEY_USAGE)
            usage = ext.value
            
            uses = []
            if usage.digital_signature:
                uses.append('Assinatura Digital')
            if usage.key_agreement:
                uses.append('Acordo de Chaves')
            if usage.key_cert_sign:
                uses.append('Assinatura de Certificados')
            
            return uses
        except:
            return ['Não especificado']


class CertificateSelector:
    """Interface para seleção de certificados"""
    
    def __init__(self, pkcs11_manager: PKCS11Manager):
        self.manager = pkcs11_manager
    
    def select_certificate_gui(self) -> Optional[str]:
        """Interface gráfica para seleção de certificado (Streamlit)"""
        import streamlit as st
        
        st.markdown("### 🔐 Selecione o Certificado Digital")
        
        # Listar slots disponíveis
        slots = self.manager.list_available_slots()
        
        if not slots:
            st.error("Nenhum token/smartcard detectado")
            st.info("Verifique se o dispositivo está conectado")
            return None
        
        # Seletor de slot
        slot_options = {
            f"{slot['token_label']} ({slot['serial_number']})": slot['slot_id']
            for slot in slots
        }
        
        selected_slot_name = st.selectbox(
            "Token/Smartcard:",
            list(slot_options.keys())
        )
        
        selected_slot = slot_options[selected_slot_name]
        
        # PIN
        pin = st.text_input("PIN:", type="password", max_chars=20)
        
        if st.button("🔓 Acessar Certificados"):
            if not pin:
                st.error("Digite o PIN")
                return None
            
            # Abrir sessão e fazer login
            if not self.manager.open_session(selected_slot):
                st.error("Erro ao abrir sessão com o token")
                return None
            
            if not self.manager.login(pin):
                st.error("PIN incorreto")
                self.manager.close_session()
                return None
            
            # Listar certificados
            certificates = self.manager.list_certificates()
            
            if not certificates:
                st.error("Nenhum certificado encontrado")
                self.manager.close_session()
                return None
            
            # Mostrar certificados
            st.markdown("### 📜 Certificados Disponíveis")
            
            for cert in certificates:
                with st.expander(f"{cert['label']} - {cert['subject'].get('CN', 'Sem nome')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Titular:**", cert['subject'].get('CN', '-'))
                        st.write("**CPF/CNPJ:**", cert['subject'].get('CPF', '-'))
                        st.write("**Emissor:**", cert['issuer'].get('CN', '-'))
                    
                    with col2:
                        st.write("**Válido de:**", cert['not_before'])
                        st.write("**Válido até:**", cert['not_after'])
                        st.write("**Status:**", "✅ Válido" if cert['is_valid'] else "❌ Expirado")
                    
                    if st.button(f"Usar este certificado", key=cert['id']):
                        st.session_state.selected_certificate = cert['id']
                        st.success(f"Certificado selecionado: {cert['label']}")
                        return cert['id']
        
        return None


# Exemplo de uso
if __name__ == "__main__":
    # Testar detecção de biblioteca
    manager = PKCS11Manager()
    
    if manager.lib_path:
        print(f"✅ Biblioteca PKCS#11 encontrada: {manager.lib_path}")
        
        # Listar slots
        slots = manager.list_available_slots()
        print(f"\n📟 Slots disponíveis: {len(slots)}")
        
        for slot in slots:
            print(f"  - {slot['token_label']} (S/N: {slot['serial_number']})")
    else:
        print("❌ Nenhuma biblioteca PKCS#11 encontrada")
        print("Instale o driver do seu token/smartcard")