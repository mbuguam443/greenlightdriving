import { NavigatorScreenParams } from '@react-navigation/native';

export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
};

export type HomeStackParamList = {
  Dashboard: undefined;
  Lessons: undefined;
  Schedule: undefined;
  Payments: undefined;
  Progress: undefined;
  Events: undefined;
  Documents: undefined;
};

export type AppTabsParamList = {
  HomeTab: NavigatorScreenParams<HomeStackParamList>;
  PaymentsTab: undefined;
  NotificationsTab: undefined;
  MoreTab: NavigatorScreenParams<MoreStackParamList>;
};

export type MoreStackParamList = {
  More: undefined;
  Profile: undefined;
};

export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  App: NavigatorScreenParams<AppTabsParamList>;
};
