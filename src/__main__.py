from dotenv import load_dotenv
from utils import load_config


load_dotenv()
load_config()


if __name__ == "__main__":
    from run import main
    main()
