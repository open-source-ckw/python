from nest.core import Injectable
import json
from libs.conf.service import ConfService
from libs.jwt.guard import JwtGuard
from libs.jwt.service import JwtService
from libs.log.service import LogService
        
@Injectable
class AiProjectService:
    def __init__(self, conf: ConfService, log: LogService, service: JwtService, guard: JwtGuard):
        self.conf = conf
        self.log = log
        self.service = service
        self.guard = guard
        
    
    def hello(self):
        return self.issue()
        #return self.verify()
        #return self.refresh()
    
    def issue(self):
        """
        working HS256 token
        {"access": "eyJhbGciOiJIUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoiYWNjZXNzIiwiaWF0IjoxNzU4NTM1MjEwLCJleHAiOjE3NTg2MjE2MTAsImp0aSI6IjAzYzVjMmZlOGUxMTRiNzViN2YzZjRhYmQzZmQ4N2Q3IiwiYXUiOjI4NzMyMTksInVuYW1lIjoibnBhcm1hciJ9.Wh6I0w0RCOe1stnABIEVPTnY-bGL9UprJjDLvyVM_Tw", "refresh": "eyJhbGciOiJIUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoicmVmcmVzaCIsImlhdCI6MTc1ODUzNTIxMCwiZXhwIjoxNzU5MTQwMDEwLCJqdGkiOiJkNzRjMzRmZDY1ODg0MWFhOGZmOTJmY2NjNmI2NTk1YyIsImF1IjoyODczMjE5LCJzZXNzIjp7ImlkIjoiUy0yODczMjE5In19.PlZnU_-XlBKbc-B5djqF4AyqPJGk49z8tqoJbzcePU8"}

        working RS256 token
        {"access": "eyJhbGciOiJSUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoiYWNjZXNzIiwiaWF0IjoxNzU4NTYyMDM1LCJleHAiOjE3NTg2NDg0MzUsImp0aSI6IjhiNGQxYjRiMjdhNjQ0MTI5YzUyYjhlMTEzOGEyYTFiIiwiYXUiOjI4NzMyMTksInVuYW1lIjoibnBhcm1hciJ9.M0lxITv3HKWCsuFaQsEPuMguAkCsv3JjGoS4IHbQcY3WTsYwsnxHe8E_hqONpwZFSWy88erDNdwpYaIcMeyRoPkwEERFNIkWylr4r9qunK3ZovyvFN0MymL1MYBaRUBtE2lY0IezN813biqk6NzLZKHT84a-8fKqTFPQrgbCASnHYXHG3RHKW-2YmCivQ4gln5I81ThJuYX0zoxN-h5G2WoOugomAxBHj_8te5nU2gZvCi1J392tpkoau-2MGnbgAOW01MctxBOK6C70_fHF5K9Tlkzut3C-eUAv-7hR_9V_qnkR-mdchcy03GJJHGOOKt3y2Xa6EF9cqSk7yXRmLg", "refresh": "eyJhbGciOiJSUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoicmVmcmVzaCIsImlhdCI6MTc1ODU2MjAzNiwiZXhwIjoxNzU5MTY2ODM2LCJqdGkiOiI1MzhlNzAyNGE3MTY0NDEyYTVkMzYyZmM3MzZlZDQ5NSIsImF1IjoyODczMjE5LCJzZXNzIjp7ImlkIjoiUy0yODczMjE5In19.mxi-3q6N1BYKc2HClW7RHv5II0PzfJ9_LsP3cLRUO0qdXuZkJ8iWVktqZmAt6Nw3qrjurZkefJQctCszZ3xXX6q4xlDpiQW_4UJ2F3H6t7w0EbLqiqOOK3UmQVSz4BN4K4pXO578KlCfEMwYZsOUVUppWP98Z6n0r6P07OxWMgtWExPwujzTuNpymWQ-4mF7ZoTZnnoAW_rUR4WHRHLjUpeRgCZhk2dVo2LB5HRSwQ5Y_Vmwr_1yrtItOJyvxsxgwKnRXmkjZRNbjW_W8vtAUvrJS2Jqse5FOts3VMnarSV3fmkttxp4Rcz8RcoHRn5NCOpd1MZb8oee_-yoKuzmgQ"}
        """
        access = self.service.sign_access(
            sub=347378434,
            au=2873219,
            payload_overrides={"uname": 'nparmar'},  # optional extras
        )
        refresh = self.service.sign_refresh(
            sub=347378434,
            au=2873219,
            payload_overrides={"sess": {"id": f"S-2873219"}},  # optional
        )
        json: dict = {"access": access, "refresh": refresh}
        return json;

    def verify(self):
        tkn = '{"access": "eyJhbGciOiJSUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoiYWNjZXNzIiwiaWF0IjoxNzU4NDk3MjE1LCJleHAiOjE3NTg1ODM2MTUsImp0aSI6IjBiMTgzYmI5OTg3YTRhZTliOTBmMTQ2YmIxMmEwYjlkIiwiYXUiOjI4NzMyMTksInVuYW1lIjoibnBhcm1hciJ9.P2kyUBFr2NMjmlN6KAjuvz_YPXPzOAkjjskZRvrhvScD2pGCZgWvpraAQFYMK6lVzZ7RS0lvXeFjketpL9S-MoxUO2HE5cKnN8se3W0fyDJYi-nh9P4DvSXRJZof3edjfiOGck3lCNIEGbh4g8sPQzTM0qABUa_YeHgzn-cn3rIOkIYgQOwf2LtMtajKQdo7N5Jh-xTce5NPMT39Pb9E3zpssp8XFXYYh_QOdpy4j4Xk_EyqRwwhah1cuOMlwgrq6J8OdpWVm15PgWdusfsL0ZdOCc0k25QVGDJNtfbiA4tVmmtV_kinVb7QZ6BG9pz2uIQf_Ck8iUPfWVOBYNFCsA", "refresh": "eyJhbGciOiJSUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoicmVmcmVzaCIsImlhdCI6MTc1ODQ5NzIxNSwiZXhwIjoxNzU5MTAyMDE1LCJqdGkiOiJiYmU2M2U2MjM2ODA0MTk1YTg0YzM2OGEwMDQ0ZDk2ZSIsImF1IjoyODczMjE5LCJzZXNzIjp7ImlkIjoiUy0yODczMjE5In19.kqwb8tPLGASzsJ7Xhtl1mChDIEipHTWA7RN2JcG7Uy7XThYCFDuVP1X-voyaVYMnjgyee1t4DYXtiqXduQTtO3xCoyFuRc2Fy-6ILxjnJEj_-NrOub3jG_TltV0rOrtKV0MUnCWiz8LpAMNj1Zpd-mAsbnf9veL1z4T7pi-lOwwqEBvTdoEujoCHRhFmGvrGgFZy81mU7XwtL4LZLosYuZpJ4CX187uRFAWNR8vzaeU4gN3x7Pvyn6JjVmeFnELguTIqXUlLnF8kNI9bvbPagmLevmA2xIgb-8LpHJROYcrcl5VF05vUPs6s-YQUFzoPF1n50tHgw_OjJllgbXmS5g"}'
        tkn2 = '{"access": "eyJhbGciOiJSUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoiYWNjZXNzIiwiaWF0IjoxNzU4NDk4NzQ5LCJleHAiOjE3NTg1ODUxNDksImp0aSI6ImZkODhkYzIwYmJiOTRiMTRhNjJjNDcwN2U4NThjNWMzIiwiYXUiOjI4NzMyMTksInNlc3MiOnsiaWQiOiJTLTI4NzMyMTkifX0.TzeMmgcJlV-hM20o3KkmWlPyoNjv353JvqVL_J9JXRXLSUDeh81bAbqmgkdeahZplRt0s0s4xDn8tFyuVjaLVs6S3WjufzPu_X2eylwmXvdJfI2OOtgVn3IbKJaHWt2y8u5g7a7pqXeRU9zK439Q-d1Ppa2FriFQTi1-FdbUqJAHMRRg3xoq1Jf-qS1Zg6xmVjG3EadZEr3XO_cV60ryBZsg2hgxZT2hpWRWOHRTOiaPY4vZ_W-p9AplQojHWSdYXnZqV3t2Goi5GqOUkd-1iyF-bmcFHoQ7yl2cJDyuLxjsVsyv20rjsK3PXbRlWKWKi--i-WKa-hcXX1rI8ixYQA", "refresh": "eyJhbGciOiJSUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoicmVmcmVzaCIsImlhdCI6MTc1ODQ5ODc0OSwiZXhwIjoxNzU5MTAzNTQ5LCJqdGkiOiJjMWY2YTcyZGU2M2M0MGQxODU2MTQ5NWY5ZWE2YzM1NyIsImF1IjoyODczMjE5LCJzZXNzIjp7ImlkIjoiUy0yODczMjE5In19.bXKtywX-MxNnuB00h6C2NSZYSJVi8Qbd_6Glm7YJKCezXQ0hKobKslkv0d2lGzFFxfnIWBtVkatlakj9R00P01R3RrqYTvngVMNvook9edLAXxjBUngFWT-m8HbN_ppteaeHem6tvjMFzxzVkmi8_8hDOhyaRlZ5TeFidWpvWw1-pgMT5ObQED5aYeelDP6o4cyUxGLKTXlxfZdHFci1V-9QfrShy2IpsXihlG4J4oOc-FpaznGSYjMpvgNt1GJgDCHxCB_qt5b47WqDMRta1X2PT_5TktQ1CbzNrrNDSgjiNDb8mzQlxjHOQEG70xZqBE1-GPQ5LPNhTlWGNg0AzA"}'
        
        data = json.loads(tkn)
        data2 = json.loads(tkn2)
        
        a = self.guard.verify_access(data["access"])
        r = self.guard.verify_refresh(data["refresh"])

        a2 = self.guard.verify_access(data2["access"])
        r2 = self.guard.verify_refresh(data2["refresh"])

        t = "eyJhbGciOiJIUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoiYWNjZXNzIiwiaWF0IjoxNzU4NTM1MjEwLCJleHAiOjE3NTg2MjE2MTAsImp0aSI6IjAzYzVjMmZlOGUxMTRiNzViN2YzZjRhYmQzZmQ4N2Q3IiwiYXUiOjI4NzMyMTksInVuYW1lIjoibnBhcm1hciJ9.Wh6I0w0RCOe1stnABIEVPTnY-bGL9UprJjDLvyVM_Tw"
        ta = self.guard.verify_access(t)

        return  {"access": ta}
    
    def refresh(self):
        tkn = '{"access": "eyJhbGciOiJSUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoiYWNjZXNzIiwiaWF0IjoxNzU4NDk3MjE1LCJleHAiOjE3NTg1ODM2MTUsImp0aSI6IjBiMTgzYmI5OTg3YTRhZTliOTBmMTQ2YmIxMmEwYjlkIiwiYXUiOjI4NzMyMTksInVuYW1lIjoibnBhcm1hciJ9.P2kyUBFr2NMjmlN6KAjuvz_YPXPzOAkjjskZRvrhvScD2pGCZgWvpraAQFYMK6lVzZ7RS0lvXeFjketpL9S-MoxUO2HE5cKnN8se3W0fyDJYi-nh9P4DvSXRJZof3edjfiOGck3lCNIEGbh4g8sPQzTM0qABUa_YeHgzn-cn3rIOkIYgQOwf2LtMtajKQdo7N5Jh-xTce5NPMT39Pb9E3zpssp8XFXYYh_QOdpy4j4Xk_EyqRwwhah1cuOMlwgrq6J8OdpWVm15PgWdusfsL0ZdOCc0k25QVGDJNtfbiA4tVmmtV_kinVb7QZ6BG9pz2uIQf_Ck8iUPfWVOBYNFCsA", "refresh": "eyJhbGciOiJSUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoicmVmcmVzaCIsImlhdCI6MTc1ODQ5NzIxNSwiZXhwIjoxNzU5MTAyMDE1LCJqdGkiOiJiYmU2M2U2MjM2ODA0MTk1YTg0YzM2OGEwMDQ0ZDk2ZSIsImF1IjoyODczMjE5LCJzZXNzIjp7ImlkIjoiUy0yODczMjE5In19.kqwb8tPLGASzsJ7Xhtl1mChDIEipHTWA7RN2JcG7Uy7XThYCFDuVP1X-voyaVYMnjgyee1t4DYXtiqXduQTtO3xCoyFuRc2Fy-6ILxjnJEj_-NrOub3jG_TltV0rOrtKV0MUnCWiz8LpAMNj1Zpd-mAsbnf9veL1z4T7pi-lOwwqEBvTdoEujoCHRhFmGvrGgFZy81mU7XwtL4LZLosYuZpJ4CX187uRFAWNR8vzaeU4gN3x7Pvyn6JjVmeFnELguTIqXUlLnF8kNI9bvbPagmLevmA2xIgb-8LpHJROYcrcl5VF05vUPs6s-YQUFzoPF1n50tHgw_OjJllgbXmS5g"}'
        tkn2 = '{"access": "eyJhbGciOiJSUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoiYWNjZXNzIiwiaWF0IjoxNzU4NDk4NzQ5LCJleHAiOjE3NTg1ODUxNDksImp0aSI6ImZkODhkYzIwYmJiOTRiMTRhNjJjNDcwN2U4NThjNWMzIiwiYXUiOjI4NzMyMTksInNlc3MiOnsiaWQiOiJTLTI4NzMyMTkifX0.TzeMmgcJlV-hM20o3KkmWlPyoNjv353JvqVL_J9JXRXLSUDeh81bAbqmgkdeahZplRt0s0s4xDn8tFyuVjaLVs6S3WjufzPu_X2eylwmXvdJfI2OOtgVn3IbKJaHWt2y8u5g7a7pqXeRU9zK439Q-d1Ppa2FriFQTi1-FdbUqJAHMRRg3xoq1Jf-qS1Zg6xmVjG3EadZEr3XO_cV60ryBZsg2hgxZT2hpWRWOHRTOiaPY4vZ_W-p9AplQojHWSdYXnZqV3t2Goi5GqOUkd-1iyF-bmcFHoQ7yl2cJDyuLxjsVsyv20rjsK3PXbRlWKWKi--i-WKa-hcXX1rI8ixYQA", "refresh": "eyJhbGciOiJSUzI1NiIsImtpZCI6InYxIiwidHlwIjoiSldUIn0.eyJpc3MiOiJUSEFUU0VORCIsImF1ZCI6IkFwcGxpY2F0aW9uIiwic3ViIjoiMzQ3Mzc4NDM0IiwidHlwIjoicmVmcmVzaCIsImlhdCI6MTc1ODQ5ODc0OSwiZXhwIjoxNzU5MTAzNTQ5LCJqdGkiOiJjMWY2YTcyZGU2M2M0MGQxODU2MTQ5NWY5ZWE2YzM1NyIsImF1IjoyODczMjE5LCJzZXNzIjp7ImlkIjoiUy0yODczMjE5In19.bXKtywX-MxNnuB00h6C2NSZYSJVi8Qbd_6Glm7YJKCezXQ0hKobKslkv0d2lGzFFxfnIWBtVkatlakj9R00P01R3RrqYTvngVMNvook9edLAXxjBUngFWT-m8HbN_ppteaeHem6tvjMFzxzVkmi8_8hDOhyaRlZ5TeFidWpvWw1-pgMT5ObQED5aYeelDP6o4cyUxGLKTXlxfZdHFci1V-9QfrShy2IpsXihlG4J4oOc-FpaznGSYjMpvgNt1GJgDCHxCB_qt5b47WqDMRta1X2PT_5TktQ1CbzNrrNDSgjiNDb8mzQlxjHOQEG70xZqBE1-GPQ5LPNhTlWGNg0AzA"}'

        data = json.loads(tkn)
        data2 = json.loads(tkn2)

        return self.service.refresh(data2["access"], data["refresh"])
        #return self.service.refresh(data2["access"], data2["refresh"])
