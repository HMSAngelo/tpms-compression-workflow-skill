# TPMS 压缩技能

将本仓库里的 `tpms-compression` 文件夹完整复制到另一台设备的 Codex 用户技能目录。Windows 通常为 `%USERPROFILE%\.codex\skills\tpms-compression`。保留 `SKILL.md`、`references` 和 `scripts` 的相对位置。

技能面向 Windows 命令行工作流。执行完整流程需要你在目标机器上分别安装并配置 nTopology、HyperMesh 和 Abaqus。SolidWorks 仅用于可选的外部 CAD 环节。首次运行时请核对各程序的路径、版本及授权，并用小工况验证网格和求解交接。

仓库保留原技能快照。流程参考和个别示例适配器含旧 HPS180 工况或本机目录。目标机器需要提供自己的 nTopology notebook、工况输入和工作目录；历史路径不能直接作为可运行的示例。请按 `tpms-compression/references/workflow.md` 逐步核对。本仓库不包含商业软件、授权文件、试件网格或仿真结果。
