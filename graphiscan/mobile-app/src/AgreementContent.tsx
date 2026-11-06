import React from 'react'
import { Text, View } from 'react-native'
import { Body, styles, useColors } from './ui'

// Hide the redundant version-history explanation; acceptance still uses the server notice version.
export default function AgreementContent({ content }: { content: string }) {
  const colors = useColors()
  return <View style={{ gap: 16 }}>{content.split(/\r?\n\s*\r?\n/).filter(paragraph => paragraph.trim() !== 'A newly published notice requires a new acknowledgement. Earlier acceptances remain associated with their original versions.').map((paragraph, index) =>
    /^\d+\.\s+[^\r\n]+$/.test(paragraph.trim())
      ? <Text key={index} accessibilityRole="header" style={[styles.body, { color: colors.text, fontWeight: '700', marginTop: index ? 8 : 0 }]}>{paragraph}</Text>
      : <Body key={index}>{paragraph}</Body>
  )}</View>
}
