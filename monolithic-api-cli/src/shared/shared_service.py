from nest.core import Injectable
        
@Injectable
class SharedService:
    
    
    def hello(self):
        print("Hello from SharedService")
