import sys
from classify import process_classification
from link import process_linking
from build_graph import build_graph

def main():
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py [classify|link|process]")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == "classify":
        process_classification()
    elif command == "link":
        process_linking()
    elif command == "process":
        process_classification()
        process_linking()
        build_graph()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python pipeline.py [classify|link|process]")

if __name__ == "__main__":
    main()
