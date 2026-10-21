import React from 'react'
import { useColorScheme } from 'react-native'
import { NavigationContainer, DarkTheme, DefaultTheme } from '@react-navigation/native'
import { createNativeStackNavigator } from '@react-navigation/native-stack'
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs'
import { SafeAreaProvider } from 'react-native-safe-area-context'
import MaterialIcons from '@expo/vector-icons/MaterialIcons'
import { StatusBar } from 'expo-status-bar'
import { SessionProvider, useSession } from './src/session'
import type { RootRoutes } from './src/navigation-types'
import { LoginScreen, ForgotPasswordScreen, ResetPasswordScreen } from './src/screens/Access'
import { HomeScreen, StudentsScreen, ResultsScreen, ProgressScreen, ProfileScreen } from './src/screens/Records'
import { StudentAddScreen } from './src/screens/StudentAdd'
import { UploadScreen } from './src/screens/Upload'
import { ResultScreen } from './src/screens/Result'
import { useColors } from './src/ui'
import HostedApp from './src/HostedApp'

const Stack = createNativeStackNavigator<RootRoutes>()
const Tabs = createBottomTabNavigator()
function MainTabs() {
  const { user } = useSession(), colors = useColors()
  const icons: Record<string, React.ComponentProps<typeof MaterialIcons>['name']> = { Home: 'home', Students: 'groups', Upload: 'upload-file', Results: 'assignment', Profile: 'person' }
  return <Tabs.Navigator screenOptions={({ route }) => ({ tabBarActiveTintColor: colors.primary, tabBarInactiveTintColor: colors.muted,
    tabBarStyle: { backgroundColor: colors.surface }, tabBarIcon: ({ color, size }) => <MaterialIcons name={icons[route.name]} size={size} color={color} /> })}>
    <Tabs.Screen name="Home" component={HomeScreen} options={{ title: 'GraphiScan' }} />
    {user!.role === 'teacher' && <Tabs.Screen name="Students" component={StudentsScreen} />}
    {user!.role === 'teacher' && <Tabs.Screen name="Upload" component={UploadScreen} />}
    <Tabs.Screen name="Results" component={ResultsScreen} options={{ title: user!.role === 'expert' ? 'Reviews' : 'Results' }} />
    <Tabs.Screen name="Profile" component={ProfileScreen} />
  </Tabs.Navigator>
}
function Navigation() {
  const { user } = useSession(), dark = useColorScheme() === 'dark', colors = useColors()
  const base = dark ? DarkTheme : DefaultTheme
  return <NavigationContainer theme={{ ...base, colors: { ...base.colors, primary: colors.primary, background: colors.bg, card: colors.surface, text: colors.text, border: colors.border } }}
    linking={{ prefixes: ['graphiscan://'], config: { screens: { ResetPassword: 'reset-password' } } }}>
    <StatusBar style={dark ? 'light' : 'dark'} />
    <Stack.Navigator>{user ? <Stack.Group navigationKey={'signed-in-' + user.user_id}>
      <Stack.Screen name="Main" component={MainTabs} options={{ headerShown: false }} />
      {user.role === 'teacher' && <Stack.Screen name="AddStudent" component={StudentAddScreen} options={{ title: 'Add student' }} />}
      <Stack.Screen name="Result" component={ResultScreen} options={{ title: 'Screening result' }} />
      <Stack.Screen name="Progress" component={ProgressScreen} options={{ title: 'Student progress' }} />
    </Stack.Group> : <Stack.Group navigationKey="signed-out">
      <Stack.Screen name="Login" component={LoginScreen} options={{ title: 'GraphiScan' }} />
      <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} options={{ title: 'Forgot password' }} />
      <Stack.Screen name="ResetPassword" component={ResetPasswordScreen} options={{ title: 'Reset password' }} />
    </Stack.Group>}</Stack.Navigator>
  </NavigationContainer>
}
export default function App() { return process.env.EXPO_PUBLIC_API_MODE === 'hosted' ? <HostedApp/> : <SafeAreaProvider><SessionProvider><Navigation /></SessionProvider></SafeAreaProvider> }
