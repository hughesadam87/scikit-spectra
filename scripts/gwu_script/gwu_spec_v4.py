from gwu_controller import Controller

def main(*args):
    controller = Controller.from_namespace()
    controller.start_run()
    
    
if __name__ == '__main__':
    main()