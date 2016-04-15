import subprocess
import re
import time


class dhcpcdManager:
    def __init__(self):
        self._filePath = '/etc/dhcpcd.conf'

        with open(self._filePath, 'r') as fp:
            self._lines = fp.readlines()

    def find_interface_line(self, interface: str) -> int:
        index = 0
        for line in self._lines:
            if line.startswith('interface ' + interface):
                return index
            index += 1
        return -1

    def find_ip_line(self, index: int) -> int:
        for line in self._lines[index:]:
            if line.startswith('static ip_address='):
                return index
            index += 1
        return -1

    def find_routers_line(self, index: int) -> int:
        for line in self._lines[index:]:
            if line.startswith('static routers='):
                return index
            index += 1
        return -1

    def find_dns_line(self, index: int) -> int:
        for line in self._lines[index:]:
            if line.startswith('static domain_name_servers='):
                return index
            index += 1
        return -1

    def set_static_info(self, interface: str, ip_address: str, routers: str, domain_name_server: str,
                        netmask: str) -> int:
        try:
            iface_index = self.find_interface_line(interface)
            netmask_number = sum([bin(int(x)).count('1') for x in netmask.split('.')])

            if iface_index != -1:
                ip_index = self.find_ip_line(iface_index)
                routers_index = self.find_routers_line(iface_index)
                dns_index = self.find_dns_line(iface_index)

                if ip_index != -1 and routers_index != -1 and dns_index != -1:
                    self._lines[ip_index] = 'static ip_address=' + ip_address + '/' + str(netmask_number) + '\n'
                    self._lines[routers_index] = 'static routers=' + routers + '\n'
                    self._lines[dns_index] = 'static domain_name_servers=' + domain_name_server + '\n'
            else:
                if self._lines[len(self._lines) - 1] != '\n':
                    self._lines.append('\n')
                self._lines.append('interface ' + interface + '\n')
                self._lines.append('static ip_address=' + ip_address + '/' + str(netmask_number) + '\n')
                self._lines.append('static routers=' + routers + '\n')
                self._lines.append('static domain_name_servers=' + domain_name_server + '\n')

            with open(self._filePath, 'w') as fp:
                for line in self._lines:
                    fp.write(line)

            return 0
        except:
            return -1

    def remove_static_info(self, interface: str) -> int:
        try:
            iface_index = self.find_interface_line(interface)
            if iface_index == -1:
                return 1
            self._lines.pop(iface_index)
            ip_index = self.find_ip_line(iface_index)
            if ip_index != -1:
                self._lines.pop(ip_index)
            routers_index = self.find_routers_line(iface_index)
            if routers_index != -1:
                self._lines.pop(routers_index)
            dns_index = self.find_dns_line(iface_index)
            if dns_index != -1:
                self._lines.pop(dns_index)

            with open(self._filePath, 'w') as fp:
                for line in self._lines:
                    fp.write(line)

            return 0
        except:
            return -1


def get_wireless_interfaces() -> list:
    p = subprocess.Popen(["iwconfig"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (data, error) = p.communicate()

    result = []
    if len(data) > 0:
        paragraphs = data.decode("utf-8").split("\n\n")
        # print(paragraphs)
        for paragraph in paragraphs:
            lines = paragraph.split('\n')
            # print(lines)
            line = lines[0]
            if len(line) > 0:
                interface = line.split('    ')
                result.append(interface[0])

    return result


def get_connected_ssid(interface: str) -> str:
    p = subprocess.Popen(["iwconfig"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (data, error) = p.communicate()

    if len(data) == 0:
        return None
    paragraphs = data.decode("utf-8").split("\n\n")
    for paragraph in paragraphs:
        lines = paragraph.split('\n')
        line = lines[0]
        if line.startswith(interface):
            result = re.search('ESSID:"([A-Za-z0-9_-]+?)"', line)
            if result:
                return result.group(1)
    return None


class wpaManager:
    def __init__(self):
        self._filePath = '/etc/wpa_supplicant/wpa_supplicant.conf'
        subprocess.call(['sudo chmod 606 ' + self._filePath], shell=True)
        with open(self._filePath, 'r') as fp:
            self._lines = fp.readlines()
        # subprocess.call(['sudo chmod 600 ' + self._filePath], shell=True)

    def find_ssid_line(self, ssid: str) -> int:
        index = 0
        for line in self._lines:
            if 'ssid="' + ssid + '"' in line:
                return index
            index += 1
        return -1

    def set_wireless_info(self, interface: str, ssid: str, password: str) -> int:
        try:
            lines = ['ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n', 'update_config=1\n\n']

            subprocess.call(['sudo chmod 606 ' + self._filePath], shell=True)
            with open(self._filePath, 'w') as fp:
                for line in lines:
                    fp.write(line)

            subprocess.call(["sudo sh -c 'wpa_passphrase " + ssid + " " + password +
                             " >> /etc/wpa_supplicant/wpa_supplicant.conf'"], shell=True)
            return 0
        except:
            return -1


def refresh_dhcpcd(interface: str):
    subprocess.call(['sudo dhcpcd -n ' + interface], shell=True)


def refresh_wireless(interface: str):
    subprocess.call(['sudo', 'ifdown', interface])
    time.sleep(1)
    subprocess.call(['sudo', 'ifdown', interface])


def restart_network():
    subprocess.call(['sudo', 'service', 'etworking', 'restart'])
