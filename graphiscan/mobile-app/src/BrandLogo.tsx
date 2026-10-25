import React from 'react'
import { Image, View } from 'react-native'

export default function BrandLogo({ size }: { size: number }) {
  return <View accessible={false} style={{ width: size, height: size, borderRadius: size / 4, overflow: 'hidden' }}>
    <Image source={require('../assets/graphiscan-logo.png')} resizeMode="contain"
      style={{ width: size, height: size }} accessible={false} />
  </View>
}
