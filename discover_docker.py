

import docker


class DDOSAWorkerContainer(object):
    ddosa_worker_private_port="5691/tcp"

    def __init__(self):
        self.container=self.find_container()

    def find_container(self):
        client = docker.from_env()

        for container in client.containers.list(filters={"ancestor": "volodymyrsavchenko/docker-integral-ddosa-worker"}):
            print("found",container)
            return container
        # return first found

        raise Exception("no containers found!")

    @property
    def url(self):
        worker_port_mapping=self.container.attrs['NetworkSettings']['Ports'][self.ddosa_worker_private_port][0]

        if str(worker_port_mapping['HostIp'])=="0.0.0.0":
            url="http://127.0.0.1:"+worker_port_mapping['HostPort']
        else:
            url="http://"+worker_port_mapping['HostIp']+":"+worker_port_mapping['HostPort']
        return url 

    @property
    def ddcache_root(self):
        for mount in self.container.attrs['Mounts']:
            if mount["Destination"] == "/data/ddcache":
                return mount['Source']

if __name__=="__main__":
    c=DDOSAWorkerContainer()
    print(c.url,c.ddcache_root)
