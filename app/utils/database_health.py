"""
Database health check và connection monitoring utilities
"""
import time
import psycopg2
from sqlalchemy.exc import OperationalError
from ..extensions import db
from ..models import Report


class DatabaseHealthChecker:
    """Utility class để monitor database health và connection"""
    
    @staticmethod
    def simple_connection_check() -> dict:
        """
        Simple database connection check for Railway health endpoint
        
        Returns:
            dict: {
                'healthy': bool,
                'response_time': float,
                'error': str | None
            }
        """
        start_time = time.time()
        result = {
            'healthy': False,
            'response_time': 0.0,
            'error': None
        }
        
        try:
            # Test basic connection with minimal query
            with db.engine.connect() as conn:
                result_proxy = conn.execute(db.text("SELECT 1"))
                test_result = result_proxy.fetchone()
                
                if test_result and test_result[0] == 1:
                    result['healthy'] = True
                    
        except Exception as e:
            result['error'] = str(e)
            result['healthy'] = False
            
        result['response_time'] = time.time() - start_time
        return result
    
    @staticmethod
    def check_connection(timeout: int = 10) -> dict:
        """
        Kiểm tra kết nối database với timeout
        
        Returns:
            dict: {
                'healthy': bool,
                'response_time': float,
                'error': str | None,
                'connection_info': dict
            }
        """
        start_time = time.time()
        result = {
            'healthy': False,
            'response_time': 0.0,
            'error': None,
            'connection_info': {}
        }
        
        try:
            # Test basic connection
            with db.engine.connect() as conn:
                # Simple query to test connection
                result_proxy = conn.execute(db.text("SELECT 1 as test"))
                test_result = result_proxy.fetchone()
                
                if test_result and test_result[0] == 1:
                    result['healthy'] = True
                    
                # Get connection info
                try:
                    db_info = conn.execute(db.text("""
                        SELECT 
                            version() as version,
                            current_database() as database,
                            current_user as user,
                            inet_server_addr() as server_addr,
                            inet_server_port() as server_port
                    """)).fetchone()
                    
                    if db_info:
                        result['connection_info'] = {
                            'version': db_info[0],
                            'database': db_info[1], 
                            'user': db_info[2],
                            'server_addr': db_info[3],
                            'server_port': db_info[4]
                        }
                except:
                    pass  # Skip if can't get connection info
                    
        except Exception as e:
            result['error'] = str(e)
            result['healthy'] = False
            
        result['response_time'] = time.time() - start_time
        return result
    
    @staticmethod
    def check_ssl_connection() -> dict:
        """
        Kiểm tra cụ thể SSL connection status
        
        Returns:
            dict: {
                'ssl_enabled': bool,
                'ssl_version': str | None,
                'ssl_cipher': str | None,
                'error': str | None
            }
        """
        result = {
            'ssl_enabled': False,
            'ssl_version': None,
            'ssl_cipher': None,
            'error': None
        }
        
        try:
            with db.engine.connect() as conn:
                ssl_info = conn.execute(db.text("""
                    SELECT 
                        version() as pg_version,
                        ssl_is_used() as ssl_used,
                        ssl_version() as ssl_version,
                        ssl_cipher() as ssl_cipher
                """)).fetchone()
                
                if ssl_info:
                    result['ssl_enabled'] = ssl_info[1] if ssl_info[1] is not None else False
                    result['ssl_version'] = ssl_info[2]
                    result['ssl_cipher'] = ssl_info[3]
                    
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    @staticmethod
    def test_report_operations() -> dict:
        """
        Test basic CRUD operations với Report model
        
        Returns:
            dict: {
                'success': bool,
                'operations': dict,
                'total_time': float,
                'error': str | None
            }
        """
        start_time = time.time()
        result = {
            'success': False,
            'operations': {},
            'total_time': 0.0,
            'error': None
        }
        
        test_report_id = None
        
        try:
            # Test CREATE
            create_start = time.time()
            test_report = Report(
                html_content="<div>Health Check Test</div>",
                css_content="/* test css */",
                js_content="// test js"
            )
            db.session.add(test_report)
            db.session.commit()
            test_report_id = test_report.id
            result['operations']['create'] = {
                'success': True,
                'time': time.time() - create_start,
                'report_id': test_report_id
            }
            
            # Test READ
            read_start = time.time()
            found_report = Report.query.get(test_report_id)
            if found_report and found_report.html_content == "<div>Health Check Test</div>":
                result['operations']['read'] = {
                    'success': True,
                    'time': time.time() - read_start
                }
            else:
                result['operations']['read'] = {
                    'success': False,
                    'time': time.time() - read_start,
                    'error': 'Report not found or content mismatch'
                }
            
            # Test UPDATE
            update_start = time.time()
            found_report.html_content = "<div>Health Check Test - Updated</div>"
            db.session.commit()
            result['operations']['update'] = {
                'success': True,
                'time': time.time() - update_start
            }
            
            # Test DELETE
            delete_start = time.time()
            db.session.delete(found_report)
            db.session.commit()
            result['operations']['delete'] = {
                'success': True,
                'time': time.time() - delete_start
            }
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            
            # Cleanup nếu có lỗi
            if test_report_id:
                try:
                    cleanup_report = Report.query.get(test_report_id)
                    if cleanup_report:
                        db.session.delete(cleanup_report)
                        db.session.commit()
                except:
                    pass
            
            try:
                db.session.rollback()
            except:
                pass
                
        result['total_time'] = time.time() - start_time
        return result
    
    @staticmethod
    def get_connection_pool_status() -> dict:
        """
        Lấy thông tin về connection pool status
        
        Returns:
            dict: Pool statistics và connection info
        """
        result = {
            'pool_size': None,
            'checked_in': None,
            'checked_out': None,
            'overflow': None,
            'invalid': None,
            'error': None
        }
        
        try:
            pool = db.engine.pool
            result.update({
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            })
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    @staticmethod
    def full_health_check() -> dict:
        """
        Comprehensive health check bao gồm tất cả tests
        
        Returns:
            dict: Complete health check results
        """
        return {
            'timestamp': time.time(),
            'connection': DatabaseHealthChecker.check_connection(),
            'ssl': DatabaseHealthChecker.check_ssl_connection(),
            'operations': DatabaseHealthChecker.test_report_operations(),
            'pool': DatabaseHealthChecker.get_connection_pool_status()
        }


def print_health_status(health_data: dict) -> None:
    """Pretty print health check results"""
    print("\n" + "="*60)
    print("🏥 DATABASE HEALTH CHECK REPORT")
    print("="*60)
    
    # Connection status
    conn = health_data.get('connection', {})
    status_icon = "✅" if conn.get('healthy') else "❌"
    print(f"{status_icon} Connection: {'Healthy' if conn.get('healthy') else 'Failed'}")
    if conn.get('response_time'):
        print(f"   Response time: {conn['response_time']:.3f}s")
    if conn.get('error'):
        print(f"   Error: {conn['error']}")
    
    # SSL status
    ssl = health_data.get('ssl', {})
    ssl_icon = "🔒" if ssl.get('ssl_enabled') else "🔓"
    print(f"{ssl_icon} SSL: {'Enabled' if ssl.get('ssl_enabled') else 'Disabled'}")
    if ssl.get('ssl_version'):
        print(f"   Version: {ssl['ssl_version']}")
    if ssl.get('ssl_cipher'):
        print(f"   Cipher: {ssl['ssl_cipher']}")
    
    # Operations test
    ops = health_data.get('operations', {})
    ops_icon = "✅" if ops.get('success') else "❌"
    print(f"{ops_icon} CRUD Operations: {'Passed' if ops.get('success') else 'Failed'}")
    if ops.get('total_time'):
        print(f"   Total time: {ops['total_time']:.3f}s")
    
    # Pool status
    pool = health_data.get('pool', {})
    if pool.get('pool_size') is not None:
        print(f"🏊 Connection Pool:")
        print(f"   Size: {pool['pool_size']}")
        print(f"   Checked out: {pool['checked_out']}")
        print(f"   Checked in: {pool['checked_in']}")
        print(f"   Overflow: {pool['overflow']}")
    
    print("="*60)
