import { Result } from 'antd'

export default function ComingSoon({ title }: { title: string }) {
  return <Result status="info" title={title} subTitle="该模块正在开发中，敬请期待" />
}
