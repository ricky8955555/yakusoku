from ipaddress import IPv4Network, IPv6Network


def humanize_network_flags(network: IPv4Network | IPv6Network) -> list[str]:
    flags = []
    if network.is_global:
        flags.append("全局 (Global)")
    if network.is_link_local:
        flags.append("本地链路 (Link-local)")
    if network.is_loopback:
        flags.append("回环 (Loopback)")
    if network.is_multicast:
        flags.append("组播 (Multicast)")
    if network.is_private:
        flags.append("私有 (Private)")
    if network.is_reserved:
        flags.append("保留 (Reserved)")
    if isinstance(network, IPv6Network) and network.is_site_local:
        flags.append("站点本地 (Site-local)")
    if network.is_unspecified:
        flags.append("未指定 (Unspecified)")
    return flags
